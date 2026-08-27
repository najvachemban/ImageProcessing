import time
import logging
from datetime import datetime

from app.logging_config import setup_logging
from app.database import SessionLocal
from app.models import Job
from app.queue import redis_client, QUEUE_NAME

setup_logging()
logger = logging.getLogger("worker")


def process_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job is None:
            logger.error("Job %s not found in database, skipping", job_id)
            return

        logger.info("Picked up job %s (operation=%s)", job.job_id, job.operation)

        # Mark as PROCESSING
        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        db.commit()

        # --- Simulated processing (real SVD logic comes in Step 7) ---
        time.sleep(2)
        # --------------------------------------------------------------

        # Mark as COMPLETED
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info("Completed job %s", job.job_id)

    except Exception:
        logger.exception("Error processing job %s", job_id)
        db.rollback()
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