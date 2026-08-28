# Distributed Image Processing & Compression Platform

## What this is

A backend system for asynchronous image processing — users upload an image,
choose an operation (SVD compression, resize, format conversion, thumbnail
generation), and get a `job_id` back immediately. A pool of independent
worker processes then does the actual (CPU-heavy) processing off the request
path, while the API stays fast and responsive.

This project isn't really about image processing — it's a vehicle for
building and understanding a **production-shaped distributed system**:
job queues, worker pools, retries, idempotency, rate limiting, and the
database/queue design decisions that hold it all together.

## Why this architecture?

Image processing — especially SVD-based compression — is CPU-bound and can
take real time. Doing that work inside an HTTP request handler would block
the API and make it unable to serve other requests under load. So the system
splits into two tiers:

- **API tier (FastAPI)**: accepts uploads, validates input, writes job
  metadata to MySQL, and enqueues work onto Redis. Fast, I/O-bound, never
  blocks on processing.
- **Worker tier (independent Python processes)**: pulls jobs off the Redis
  queue, does the actual processing, and writes results back to MySQL.

This separation gives fault isolation (a worker crash doesn't take down the
API) and independent scaling (add more workers without touching the API).

## Architecture (target)

\`\`\`
React UI → FastAPI → MySQL (job metadata, source of truth)
                   → Redis (job queue)
                        ↓
              Worker 1 / Worker 2 / Worker 3
                        ↓
              Image processing (SVD / resize / convert)
                        ↓
              Result stored → MySQL updated
\`\`\`

*(This is the target shape — the project is being built incrementally, see
"Progress" below.)*

## Progress

- [x] **Day 1** — FastAPI skeleton with `/health` endpoint
- [x] **Day 1** — MySQL running in Docker; `jobs` table schema designed
      (UUID primary keys, indexed `status`/`user_id`, JSON `parameters`
      column for per-operation flexibility)
- [x] **Day 2** - Job creation endpoint (API → MySQL)
- [x] **Day 2** - Redis job queue
- [x] **Day 2** - Worker process consuming jobs from Redis (BRPOP), updating job status 
 (PENDING → PROCESSING → COMPLETED) in MySQL; structured logging added
- [x] **Day 3** - SVD compression implementation (k-rank approximation, grayscale & color modes)
- [x] **Day 3** - Results persisted to MySQL (`results` table: compression ratio, timing, output path)
- [ ] Retry logic + exponential backoff
- [ ] Idempotency handling
- [ ] Rate limiting
- [ ] React frontend
- [ ] Docker Compose (full stack)
- [ ] Tests (unit / API / integration)
- [ ] Multi-worker benchmarking

## Tech stack

| Layer         | Choice          | Why |
|---------------|-----------------|-----|
| API           | FastAPI         | Async-native, fast I/O-bound request handling |
| Database      | MySQL           | Durable source of truth; transactions for safe concurrent updates |
| Queue         | Redis           | Lightweight, fast, atomic ops for job queue + rate limiting |
| Workers       | Python (multiprocessing) | True parallelism for CPU-bound SVD work |
| Image processing | Pillow, NumPy | Standard, well-supported tooling |
| Frontend      | React           | Simple job submission/status UI |
| Containerization | Docker Compose | Reproducible multi-service local environment |

Worker process consuming jobs from Redis (BRPOP), updating job status (PENDING → PROCESSING → COMPLETED) in MySQL; structured logging added

