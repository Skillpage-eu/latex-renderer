from contextlib import asynccontextmanager
from pathlib import Path

import dotenv
from redis.asyncio import Redis
from starlette.background import BackgroundTask

dotenv.load_dotenv()

import os
import uuid
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route

from utils import (
    set_redis_status,
    save_documents_to_temp_dir,
    get_redis_status,
    render_latex,
    get_job_directory,
)


@asynccontextmanager
async def lifespan(app: Starlette):
    redis_client = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost"))
    app.state.redis = redis_client
    yield
    await app.state.redis.close()


# GET /health
async def health(request):
    return JSONResponse({"message": "OK"})


# POST /document
async def post_document(request):
    document_id = str(uuid.uuid4())
    webhook_url = request.headers.get("X-Webhook-Url")
    await set_redis_status(request.app.state.redis, document_id, "pending")
    await save_documents_to_temp_dir(request, document_id)
    task = BackgroundTask(
        render_latex,
        uuid=document_id,
        webhook_url=webhook_url,
        redis=request.app.state.redis,
    )
    return JSONResponse(
        {"message": "Document received", "document_id": document_id},
        status_code=202,
        background=task,
    )


# GET /document/{document_id}
async def get_document(request):
    document_id = request.path_params["document_id"]
    redis = request.app.state.redis
    state = await get_redis_status(redis, document_id)

    if state == "success":
        job_dir = Path(await get_job_directory(document_id))
        output_pdf_path = job_dir / "main.pdf"

        if output_pdf_path.is_file():
            return FileResponse(
                path=output_pdf_path,
                filename=f"{document_id}.pdf",
                media_type="application/pdf",
            )
        else:
            return JSONResponse(
                {
                    "document_id": document_id,
                    "state": "error",
                    "detail": "Output file not found.",
                },
                status_code=500,
            )

    if state in ["pending", "processing"]:
        return JSONResponse(
            {"document_id": document_id, "state": state},
            status_code=202,
        )
    return JSONResponse(
        {"document_id": document_id, "state": state},
        status_code=404,
    )


# GET /state/{document_id}
async def get_state(request):
    document_id = request.path_params["document_id"]
    return JSONResponse(
        {
            "document_id": document_id,
            "state": await get_redis_status(request.app.state.redis, document_id),
        }
    )


app = Starlette(
    debug=os.environ.get("DEBUG", "False") == "True",
    routes=[
        Route("/document", post_document, methods=["POST"]),
        Route("/document/{document_id}", get_document, methods=["GET"]),
        Route("/state/{document_id}", get_state, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
    ],
    lifespan=lifespan,
)
