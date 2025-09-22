import asyncio
import os
import tempfile
import aiofiles
from redis.asyncio import Redis


async def set_redis_status(redis: Redis, document_id, state):
    await redis.set(f"latex-renderer-{document_id}", state)
    return document_id


async def get_redis_status(redis: Redis, document_id):
    state = await redis.get(f"latex-renderer-{document_id}")
    return state.decode("utf-8") if state else "non-existent"


async def save_file(uploaded_file, uuid: str):
    path = await create_job_directory(uuid)
    name = uploaded_file.filename
    async with aiofiles.open(f"{path}/{name}", "wb") as f:
        while chunk := await uploaded_file.read(65536):
            await f.write(chunk)


async def save_documents_to_temp_dir(request, uuid: str):
    async with request.form() as form:
        for uploaded_file in form.getlist("document"):
            await save_file(uploaded_file, uuid)
        for uploaded_file in form.getlist("image"):
            await save_file(uploaded_file, uuid)


async def get_job_directory(uuid: str):
    return os.path.join(tempfile.gettempdir(), "latex-renderer", uuid)


async def create_job_directory(uuid: str):
    job_directory = await get_job_directory(uuid)
    os.makedirs(job_directory, exist_ok=True)
    return job_directory


async def render_latex(uuid: str, redis: Redis):
    job_directory = await get_job_directory(uuid)
    main_file = os.path.join(job_directory, "main.tex")
    if not os.path.exists(main_file):
        await set_redis_status(redis, uuid, "failed-no-main-tex")
        raise FileNotFoundError("main.tex not found")
    await set_redis_status(redis, uuid, "processing")
    process = await asyncio.create_subprocess_exec(
        "lualatex", main_file, cwd=job_directory
    )
    return_code = await process.wait()
    match return_code:
        case 0:
            await set_redis_status(redis, uuid, "success")
        case _:
            await set_redis_status(redis, uuid, "failed-latex-error")
