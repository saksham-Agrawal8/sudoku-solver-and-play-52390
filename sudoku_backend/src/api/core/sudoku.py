"""
Sudoku core logic: board validation, solver, and generator.

This module is intentionally dependency-free and purely in-memory to support
FastAPI endpoints in this service.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import random
from typing import List, Optional, Sequence, Set, Tuple

Board = List[List[int]]  # 9x9, values 0-9. 0 means empty.


@dataclass(frozen=True)
class Cell:
    """Represents a cell coordinate in the Sudoku grid."""
    r: int
    c: int


def _is_valid_value(v: int) -> bool:
    return isinstance(v, int) and 0 <= v <= 9


def _validate_shape_and_values(board: Sequence[Sequence[int]]) -> None:
    """
    Raises ValueError if the board is not a 9x9 grid of ints in range 0-9.
    """
    if not isinstance(board, Sequence) or len(board) != 9:
        raise ValueError("Board must be a 9x9 array.")
    for r in range(9):
        row = board[r]
        if not isinstance(row, Sequence) or len(row) != 9:
            raise ValueError("Board must be a 9x9 array.")
        for c in range(9):
            v = row[c]
            if not _is_valid_value(v):
                raise ValueError("Board values must be integers in range 0..9.")


def _subgrid_start(idx: int) -> int:
    return (idx // 3) * 3


def _find_conflicts(board: Sequence[Sequence[int]]) -> Set[Cell]:
    """
    Returns a set of cells that participate in any row/col/subgrid conflict.
    Only considers filled cells (1-9). Zeros never conflict.
    """
    conflicts: Set[Cell] = set()

    # Rows
    for r in range(9):
        positions_by_val = {}
        for c in range(9):
            v = board[r][c]
            if v == 0:
                continue
            positions_by_val.setdefault(v, []).append(c)
        for v, cols in positions_by_val.items():
            if len(cols) > 1:
                for c in cols:
                    conflicts.add(Cell(r=r, c=c))

    # Columns
    for c in range(9):
        positions_by_val = {}
        for r in range(9):
            v = board[r][c]
            if v == 0:
                continue
            positions_by_val.setdefault(v, []).append(r)
        for v, rows in positions_by_val.items():
            if len(rows) > 1:
                for r in rows:
                    conflicts.add(Cell(r=r, c=c))

    # Subgrids
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            positions_by_val = {}
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    v = board[r][c]
                    if v == 0:
                        continue
                    positions_by_val.setdefault(v, []).append((r, c))
            for v, coords in positions_by_val.items():
                if len(coords) > 1:
                    for (r, c) in coords:
                        conflicts.add(Cell(r=r, c=c))

    return conflicts


def validate_board(board: Sequence[Sequence[int]]) -> Tuple[bool, List[Cell]]:
    """
    Validate Sudoku constraints for the current board state.

    Returns:
        (valid, conflicts)
        - valid: True if no conflicts exist
        - conflicts: list of cells involved in any conflict
    """
    _validate_shape_and_values(board)
    conflicts = sorted(_find_conflicts(board), key=lambda x: (x.r, x.c))
    return (len(conflicts) == 0), conflicts


def _candidates(board: Board, r: int, c: int) -> List[int]:
    """Return possible values for cell (r,c) given current board."""
    used = set()

    # Row and column
    used.update(board[r][cc] for cc in range(9) if board[r][cc] != 0)
    used.update(board[rr][c] for rr in range(9) if board[rr][c] != 0)

    # Subgrid
    sr = _subgrid_start(r)
    sc = _subgrid_start(c)
    for rr in range(sr, sr + 3):
        for cc in range(sc, sc + 3):
            v = board[rr][cc]
            if v != 0:
                used.add(v)

    return [v for v in range(1, 10) if v not in used]


def _find_next_empty_mrv(board: Board) -> Optional[Tuple[int, int, List[int]]]:
    """
    Find next empty cell using MRV heuristic (minimum remaining values).
    Returns (r, c, candidates) or None if solved (no empties).
    """
    best = None
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                continue
            cand = _candidates(board, r, c)
            if best is None or len(cand) < len(best[2]):
                best = (r, c, cand)
                if len(cand) == 0:
                    return best  # immediate dead-end
                if len(cand) == 1:
                    return best  # good enough early exit
    return best


def solve_board(board: Sequence[Sequence[int]], *, randomize: bool = False, seed: int = 0) -> Tuple[bool, Optional[Board]]:
    """
    Solve a Sudoku board using backtracking.

    Args:
        board: 9x9 grid with 0 as empty.
        randomize: if True, shuffle candidate order for variety.
        seed: deterministic seed used when randomize=True.

    Returns:
        (solvable, solution_board_or_none)

    Notes:
        - If the input board is invalid (has conflicts), this returns (False, None).
        - The returned solution is a deep copy (does not mutate caller board).
    """
    valid, _conflicts = validate_board(board)
    if not valid:
        return False, None

    work: Board = [list(row) for row in board]
    rng = random.Random(seed)

    def backtrack() -> bool:
        nxt = _find_next_empty_mrv(work)
        if nxt is None:
            return True  # solved
        r, c, cand = nxt
        if len(cand) == 0:
            return False
        if randomize:
            rng.shuffle(cand)
        for v in cand:
            work[r][c] = v
            if backtrack():
                return True
            work[r][c] = 0
        return False

    solvable = backtrack()
    return solvable, deepcopy(work) if solvable else (False, None)


def _count_solutions(board: Board, *, limit: int = 2) -> int:
    """
    Count number of solutions up to `limit` (default 2).
    Used to ensure uniqueness during puzzle generation.
    """
    work = deepcopy(board)
    count = 0

    def backtrack() -> None:
        nonlocal count
        if count >= limit:
            return
        nxt = _find_next_empty_mrv(work)
        if nxt is None:
            count += 1
            return
        r, c, cand = nxt
        if len(cand) == 0:
            return
        for v in cand:
            work[r][c] = v
            backtrack()
            work[r][c] = 0
            if count >= limit:
                return

    backtrack()
    return count


def _generate_full_solution(*, seed: int = 0) -> Board:
    """
    Generate a fully solved Sudoku grid.
    Deterministic by default for reproducibility.
    """
    empty: Board = [[0 for _ in range(9)] for _ in range(9)]
    solvable, sol = solve_board(empty, randomize=True, seed=seed)
    if not solvable or sol is None:
        # Extremely unlikely; but keep safe fallback.
        raise RuntimeError("Failed to generate a solved Sudoku grid.")
    return sol


def generate_puzzle(*, difficulty: str = "easy", seed: int = 0) -> Board:
    """
    Generate a Sudoku puzzle with a unique solution.

    Args:
        difficulty: "easy" | "medium" | "hard" (others treated as "easy")
        seed: deterministic seed controlling generation.

    Returns:
        9x9 board with zeros for blanks.
    """
    difficulty = (difficulty or "easy").lower()
    # Approximate target blanks; uniqueness is enforced.
    # Tuning can be adjusted later without changing the API.
    blanks_by_difficulty = {
        "easy": 40,
        "medium": 50,
        "hard": 58,
    }
    target_blanks = blanks_by_difficulty.get(difficulty, blanks_by_difficulty["easy"])

    rng = random.Random(seed)

    puzzle = _generate_full_solution(seed=seed)

    # Create removal order deterministically from RNG.
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)

    removed = 0
    for (r, c) in cells:
        if removed >= target_blanks:
            break
        if puzzle[r][c] == 0:
            continue

        backup = puzzle[r][c]
        puzzle[r][c] = 0

        # Ensure uniqueness: count solutions up to 2.
        sol_count = _count_solutions(puzzle, limit=2)
        if sol_count != 1:
            puzzle[r][c] = backup  # revert
            continue
        removed += 1

    return puzzle
