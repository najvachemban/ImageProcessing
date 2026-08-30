import time
import logging
import os
from datetime import datetime

from app.logging_config import setup_logging
from app.database import SessionLocal
from app.models import Job
from app.queue import redis_client, QUEUE_NAME
from app.processing import compress_image_dct
from app.models import Job, Result

setup_logging()
logger = logging.getLogger("worker")

RESULTS_DIR = "results"
UPLOAD_DIR = "uploads"
os.makedirs(RESULTS_DIR, exist_ok=True)

def process_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job is None:
            logger.error("Job %s not found in database, skipping", job_id)
            return

        logger.info("Picked up job %s (operation=%s)", job.job_id, job.operation)

        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        db.commit()

        input_path = os.path.join(UPLOAD_DIR, job.filename)
        output_filename = f"compressed_{job.filename}"
        output_path = os.path.join(RESULTS_DIR, output_filename)

        if job.operation == "dct_compress":
            quality = (job.parameters or {}).get("quality", 50)
            mode = (job.parameters or {}).get("mode", "grayscale")
            stats = compress_image_dct(input_path, output_path, quality, mode=mode)
            logger.info(
                "DCT compression done for job %s: mode=%s quality=%s ratio=%sx time=%ss",
                job.job_id, stats["mode"], stats["quality_used"], stats["compression_ratio"], stats["processing_time_seconds"],
            )

            result = Result(
                job_id=job.job_id,
                output_path=output_path,
                original_size_bytes=stats["original_size_bytes"],
                compressed_size_bytes=stats["compressed_size_bytes"],
                compression_ratio=stats["compression_ratio"],
                processing_time_seconds=stats["processing_time_seconds"],
                parameters_used=job.parameters,
            )
            db.add(result)
        else:
            logger.warning("Operation '%s' not yet implemented, skipping processing", job.operation)
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info("Completed job %s", job.job_id)

    except Exception:
        logger.exception("Error processing job %s", job_id)
        db.rollback()
        job.status = "FAILED"
        db.commit()
    finally:
        db.close()


def run_worker() -> None:
    logger.info("Worker started. Listening on queue '%s'...", QUEUE_NAME)
    while True:
        # BRPOP blocks until an item is available; returns (queue_name, value)
        _, job_id = redis_client.brpop(QUEUE_NAME)
        process_job(job_id)


if __name__ == "__main__":
    run_worker()