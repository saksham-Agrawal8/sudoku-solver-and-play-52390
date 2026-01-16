from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.sudoku import router as sudoku_router

openapi_tags = [
    {
        "name": "health",
        "description": "Basic service health endpoints.",
    },
    {
        "name": "sudoku",
        "description": "Sudoku validation, solving, and puzzle generation.",
    },
]

app = FastAPI(
    title="Sudoku Backend API",
    description=(
        "In-memory Sudoku API for validating boards, solving puzzles, and generating new puzzles.\n\n"
        "Frontend usage:\n"
        "- Generate: GET /generate?difficulty=easy|medium|hard\n"
        "- Validate: POST /validate\n"
        "- Solve: POST /solve\n"
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Permissive CORS for local development frontend (React on :3000).
# We keep allow_origins=["*"] as well to avoid environment friction while developing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Simple health check endpoint to verify the API is running.",
    operation_id="health_check",
)
# PUBLIC_INTERFACE
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON payload indicating service health.
    """
    return {"message": "Healthy"}


@app.get(
    "/docs/help",
    tags=["health"],
    summary="API usage help",
    description="Quick usage notes for the Sudoku endpoints.",
    operation_id="docs_help",
)
# PUBLIC_INTERFACE
def docs_help():
    """
    Provide brief usage notes for this API.

    Returns:
        JSON payload with example request shapes and endpoints.
    """
    return {
        "endpoints": {
            "GET /generate": {"query": {"difficulty": "easy|medium|hard"}, "returns": {"board": "number[9][9]"}},
            "POST /validate": {"body": {"board": "number[9][9]"}, "returns": {"valid": "boolean", "conflicts?": "..."}},
            "POST /solve": {"body": {"board": "number[9][9]"}, "returns": {"solvable": "boolean", "solution?": "number[9][9]"}},
        }
    }


# Sudoku endpoints
app.include_router(sudoku_router)
