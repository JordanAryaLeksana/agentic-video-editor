from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobType(str, Enum):
    GENERATE_THUMBNAIL = "generate_thumbnail"



@dataclass(frozen=True, slots=True)
class ProcessingJob:
    id:UUID
    media_id:UUID
    job_type:JobType
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1"
            )

        if not 0 <= self.attempts <= self.max_attempts:
            raise ValueError(
                "Invalid number of attempts"
            )

        