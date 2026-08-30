import os
import uuid
import json
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Job
from app.schemas import JobCreateResponse
from app.queue import enqueue_job

app = FastAPI(title="Distributed Image Processing Platform")

UPLOAD_DIR = "uploads"
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_OPERATIONS = {"dct_compress", "resize", "convert", "thumbnail"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.post("/jobs", response_model=JobCreateResponse, status_code=201)
async def create_job(
    file: UploadFile = File(...),
    operation: str = Form(...),
    parameters: str = Form("{}"),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1. Validate operation
    if operation not in ALLOWED_OPERATIONS:
        raise HTTPException(status_code=400, detail=f"Invalid operation. Must be one of {ALLOWED_OPERATIONS}")

    # 2. Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG/JPEG images are supported")

    # 3. Read and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    # 4. Parse parameters JSON (e.g. {"k": 50} for SVD)
    try:
        parsed_params = json.loads(parameters)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="parameters must be valid JSON")

    # 5. Generate job_id and save file using it (avoids filename collisions)
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{job_id}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(contents)

    # 6. Create job row
    job = Job(
        job_id=job_id,
        user_id=user_id,
        filename=saved_filename,
        operation=operation,
        parameters=parsed_params,
        status="PENDING",
    )
    db.add(job)
    db.commit()
    enqueue_job(job.job_id)

    return JobCreateResponse(job_id=job.job_id, status=job.status, operation=job.operation)

    