from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    DONE = "DONE"
    FAILED = "FAILED"


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4_000)
    critical: bool = False


class ApprovalRequest(BaseModel):
    approved: bool


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobState(JobResponse):
    task: str
    result: str | None = None
    error: str | None = None
