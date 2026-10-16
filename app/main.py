import asyncio
import json
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from redis.asyncio import Redis

from .models import ApprovalRequest, JobResponse, JobState, JobStatus, TaskRequest
from .observability import configure_observability
from .worker import job_key, process_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_observability()
    app.state.redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    yield
    await app.state.redis.aclose()


app = FastAPI(title="API de producción multi-agente", lifespan=lifespan)


@app.post("/tasks", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(payload: TaskRequest) -> JobResponse:
    job_id = str(uuid4())
    redis: Redis = app.state.redis
    await redis.hset(job_key(job_id), mapping={
        "status": JobStatus.PENDING, "task": payload.task,
        "critical": json.dumps(payload.critical),
    })
    asyncio.create_task(process_job(redis, job_id))
    return JobResponse(job_id=job_id, status=JobStatus.PENDING)


@app.get("/tasks/{job_id}", response_model=JobState)
async def get_task(job_id: str) -> JobState:
    data = await app.state.redis.hgetall(job_key(job_id))
    if not data:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return JobState(job_id=job_id, **data)


@app.post("/tasks/{job_id}/approve", response_model=JobResponse)
async def approve_task(job_id: str, payload: ApprovalRequest) -> JobResponse:
    redis: Redis = app.state.redis
    data = await redis.hgetall(job_key(job_id))
    if not data:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if data["status"] != JobStatus.WAITING_APPROVAL:
        raise HTTPException(status_code=409, detail="El job no está esperando aprobación")
    if not payload.approved:
        await redis.hset(job_key(job_id), mapping={"status": JobStatus.DONE, "result": "Tarea rechazada por la persona aprobadora."})
        return JobResponse(job_id=job_id, status=JobStatus.DONE)
    asyncio.create_task(process_job(redis, job_id, resume=True))
    return JobResponse(job_id=job_id, status=JobStatus.PENDING)
