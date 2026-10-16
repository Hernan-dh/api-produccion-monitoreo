import json
import os

from redis.asyncio import Redis

from .graph import run_graph
from .models import JobStatus


def job_key(job_id: str) -> str:
    return f"jobs:{job_id}"


async def update(redis: Redis, job_id: str, **fields: str) -> None:
    await redis.hset(job_key(job_id), mapping=fields)


async def process_job(redis: Redis, job_id: str, resume: bool = False) -> None:
    """Worker desacoplado del endpoint: cualquier error queda visible como FAILED."""
    raw = await redis.hgetall(job_key(job_id))
    if not raw:
        return
    await update(redis, job_id, status=JobStatus.RUNNING)
    try:
        state = await run_graph(
            os.environ["REDIS_URL"], job_id, raw["task"],
            raw.get("critical", "false") == "true", resume,
        )
        if "__interrupt__" in state:
            await update(redis, job_id, status=JobStatus.WAITING_APPROVAL)
            return
        await update(redis, job_id, status=JobStatus.DONE, result=state.get("result", ""))
    except Exception as exc:
        await update(redis, job_id, status=JobStatus.FAILED, error=str(exc))
