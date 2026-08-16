from fastapi import FastAPI

app = FastAPI(title="Distributed Image Processing Platform")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness check for the API service."""
    return {"status": "ok"}