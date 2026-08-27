from pydantic import BaseModel


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    operation: str