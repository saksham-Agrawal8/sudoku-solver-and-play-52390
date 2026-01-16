from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.core.sudoku import generate_puzzle, solve_board, validate_board
from src.api.models.sudoku import (
    GenerateResponse,
    SolveRequest,
    SolveResponse,
    ValidateRequest,
    ValidateResponse,
)

router = APIRouter(prefix="", tags=["sudoku"])


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate a Sudoku board",
    description=(
        "Checks the current board state for Sudoku rule conflicts.\n\n"
        "- Input must be a 9x9 grid of integers 0..9.\n"
        "- Zeros are treated as empty cells.\n"
        "- Conflicts include any duplicates in a row, column, or 3x3 subgrid."
    ),
    operation_id="sudoku_validate",
)
# PUBLIC_INTERFACE
def validate_endpoint(payload: ValidateRequest) -> ValidateResponse:
    """
    Validate Sudoku board constraints.

    Args:
        payload: ValidateRequest containing a 9x9 board (0..9).

    Returns:
        ValidateResponse indicating whether the board is valid; if invalid,
        returns a list of conflict cell coordinates.
    """
    try:
        valid, conflicts = validate_board(payload.board)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if valid:
        return ValidateResponse(valid=True, conflicts=None, message="Board is valid.")

    return ValidateResponse(
        valid=False,
        conflicts={"cells": [{"r": cell.r, "c": cell.c} for cell in conflicts]},
        message="Board has conflicts.",
    )


@router.post(
    "/solve",
    response_model=SolveResponse,
    summary="Solve a Sudoku board",
    description=(
        "Attempts to solve the given Sudoku board using backtracking.\n\n"
        "- Input must be a 9x9 grid of integers 0..9.\n"
        "- If the board has conflicts, it is treated as unsolvable.\n"
        "- Returns a full solved board when solvable=true."
    ),
    operation_id="sudoku_solve",
)
# PUBLIC_INTERFACE
def solve_endpoint(payload: SolveRequest) -> SolveResponse:
    """
    Solve a Sudoku puzzle.

    Args:
        payload: SolveRequest containing a 9x9 board (0..9).

    Returns:
        SolveResponse with solvable flag and solution when solvable=true.
    """
    try:
        solvable, solution = solve_board(payload.board, randomize=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if not solvable or solution is None:
        return SolveResponse(solvable=False, solution=None, message="Board is not solvable.")

    return SolveResponse(solvable=True, solution=solution, message="Solved successfully.")


@router.get(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate a Sudoku puzzle",
    description=(
        "Generates a new Sudoku puzzle.\n\n"
        "- Returns a 9x9 grid.\n"
        "- Empty cells are represented by 0.\n"
        "- Difficulty controls approximate number of blanks while keeping a unique solution."
    ),
    operation_id="sudoku_generate",
)
# PUBLIC_INTERFACE
def generate_endpoint(
    difficulty: str = Query(
        default="easy",
        description="Puzzle difficulty: easy | medium | hard",
        pattern="^(easy|medium|hard)$",
    )
) -> GenerateResponse:
    """
    Generate a Sudoku puzzle.

    Args:
        difficulty: Requested difficulty level (easy/medium/hard).

    Returns:
        GenerateResponse containing a generated 9x9 board with 0 for blanks.
    """
    # Deterministic seed per difficulty for stable behavior; can be enhanced later.
    seed_map = {"easy": 0, "medium": 1, "hard": 2}
    seed = seed_map.get((difficulty or "easy").lower(), 0)

    try:
        board = generate_puzzle(difficulty=difficulty, seed=seed)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Failed to generate puzzle.") from e

    return GenerateResponse(board=board)
