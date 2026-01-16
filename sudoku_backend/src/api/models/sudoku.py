from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, field_validator


Board = List[List[int]]


def _validate_board_shape_and_values(board: Board) -> Board:
    if len(board) != 9 or any(len(row) != 9 for row in board):
        raise ValueError("Board must be a 9x9 array.")
    for row in board:
        for v in row:
            if not isinstance(v, int) or v < 0 or v > 9:
                raise ValueError("Board values must be integers in range 0..9.")
    return board


class SudokuCell(BaseModel):
    r: int = Field(..., ge=0, le=8, description="Row index (0-8).")
    c: int = Field(..., ge=0, le=8, description="Column index (0-8).")


class ValidateRequest(BaseModel):
    board: Board = Field(..., description="9x9 Sudoku board; 0 indicates empty cell.")

    @field_validator("board")
    @classmethod
    def validate_board(cls, v: Board) -> Board:
        return _validate_board_shape_and_values(v)


class ValidateConflicts(BaseModel):
    cells: List[SudokuCell] = Field(..., description="Cells involved in conflicts.")


class ValidateResponse(BaseModel):
    valid: bool = Field(..., description="True if the board has no conflicts.")
    conflicts: Optional[ValidateConflicts] = Field(
        default=None, description="Conflict details when valid=false."
    )
    message: Optional[str] = Field(default=None, description="Optional human-readable message.")


class SolveRequest(BaseModel):
    board: Board = Field(..., description="9x9 Sudoku board; 0 indicates empty cell.")

    @field_validator("board")
    @classmethod
    def validate_board(cls, v: Board) -> Board:
        return _validate_board_shape_and_values(v)


class SolveResponse(BaseModel):
    solvable: bool = Field(..., description="True if the board is solvable.")
    solution: Optional[Board] = Field(
        default=None, description="Solved 9x9 board when solvable=true."
    )
    message: Optional[str] = Field(default=None, description="Optional human-readable message.")


class GenerateResponse(BaseModel):
    board: Board = Field(..., description="Generated 9x9 Sudoku board; 0 indicates empty cell.")


Difficulty = Literal["easy", "medium", "hard"]
