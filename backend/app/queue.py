import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
QUEUE_NAME = os.getenv("QUEUE_NAME", "image_jobs_queue")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def enqueue_job(job_id: str) -> None:
    """Push a job_id onto the processing queue for workers to consume."""
    redis_client.lpush(QUEUE_NAME, job_id)