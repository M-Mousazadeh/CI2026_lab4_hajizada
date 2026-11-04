"""Lab 4: generalized Klotski, optimal single-cell slide solver (BFS).

Python 3.10+, standard library only. Board coordinates are zero-based.
Usage: python solver.py --all
       python solver.py --problem p04 --show-boards
"""
from __future__ import annotations
import argparse
from collections import deque, defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


@dataclass(frozen=True)
class Problem:
    name: str
    rows: int
    cols: int
    exit_columns: tuple[int, ...]
    target: str
    names: tuple[str, ...]
    shapes: tuple[tuple[int, int], ...]
    initial: tuple[int, ...]  # top-left offset (row * cols + col), per piece


def parse_problems(path: Path) -> dict[str, Problem]:
    text = path.read_text(encoding='utf-8')
    chunks = text.split('problem ')[1:]
    result = {}
    for chunk in chunks:
        lines = [s.strip() for s in chunk.splitlines() if s.strip() and not s.strip().startswith('#')]
        name = lines[0]
        rows, cols = map(int, lines[1].split()[1:])
        exit_line = lines[2].split()
        assert exit_line[:2] == ['exit', 'bottom']
        exit_cols = tuple(map(int, exit_line[2:]))
        target = lines[3].split()[1]
        separators = [i for i, s in enumerate(lines) if s == '=========']
        grid = [line.split() for line in lines[separators[0]+1:separators[1]]]
        assert len(grid) == rows and all(len(row) == cols for row in grid)
        coords = defaultdict(list)
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell != '.':
                    coords[cell].append((r, c))
        names = (target,) + tuple(sorted(n for n in coords if n != target))
        shapes, initial = [], []
        for n in names:
            cells = coords[n]
            rmin, cmin = min(r for r, c in cells), min(c for r, c in cells)
            height = max(r for r, c in cells) - rmin + 1
            width = max(c for r, c in cells) - cmin + 1
            if len(cells) != height*width:
                raise ValueError(f'{name}: piece {n} is not rectangular')
            shapes.append((height, width))
            initial.append(rmin*cols+cmin)
        if len(exit_cols) != shapes[0][1]:
            raise ValueError(f'{name}: exit width does not match target')
        result[name] = Problem(name, rows, cols, exit_cols, target, names,
                               tuple(shapes), tuple(initial))
    return result


DIRECTIONS = ((-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right'))


def canonical_key(p: Problem, state: tuple[int, ...]) -> tuple:
    """Collapse label permutations of same-sized, non-target pieces.

    This is safe because pieces of identical dimensions are interchangeable
    for collision avoidance and for the target goal.
    """
    groups = defaultdict(list)
    for i in range(1, len(state)):
        groups[p.shapes[i]].append(state[i])
    return (state[0], tuple((shape, tuple(sorted(positions)))
                            for shape, positions in sorted(groups.items())))


def goal_test(p: Problem, state: tuple[int, ...]) -> bool:
    target_row, target_col = divmod(state[0], p.cols)
    height, width = p.shapes[0]
    return (target_row + height == p.rows and
            tuple(range(target_col, target_col+width)) == p.exit_columns)


def occupancy(p: Problem, state: tuple[int, ...]) -> list[int]:
    cells = [-1] * (p.rows * p.cols)
    for i, (pos, (height, width)) in enumerate(zip(state, p.shapes)):
        r, c = divmod(pos, p.cols)
        for rr in range(r, r+height):
            for cc in range(c, c+width):
                idx = rr*p.cols+cc
                if cells[idx] != -1:
                    raise ValueError('Overlapping pieces')
                cells[idx] = i
    return cells


def successors(p: Problem, state: tuple[int, ...]):
    occupied = occupancy(p, state)
    for i, (pos, (height, width)) in enumerate(zip(state, p.shapes)):
        r, c = divmod(pos, p.cols)
        for dr, dc, direction in DIRECTIONS:
            nr, nc = r+dr, c+dc
            if not (0 <= nr and 0 <= nc and nr+height <= p.rows and nc+width <= p.cols):
                continue
            # Check all destination cells, allowing overlap with this same piece.
            if any(occupied[rr*p.cols+cc] not in (-1, i)
                   for rr in range(nr, nr+height)
                   for cc in range(nc, nc+width)):
                continue
            next_state = list(state)
            next_state[i] = nr*p.cols+nc
            yield tuple(next_state), (p.names[i], direction)


def solve(p: Problem, max_states: int = 3_000_000):
    start_time = perf_counter()
    start = p.initial
    start_key = canonical_key(p, start)
    # Parent dictionary stores (parent canonical key, move, concrete board).
    parents = {start_key: (None, None, start)}
    frontier = deque([start_key])
    expanded = 0
    while frontier:
        key = frontier.popleft()
        parent, action, state = parents[key]
        expanded += 1
        if goal_test(p, state):
            moves = []
            states = [state]
            while parents[key][0] is not None:
                prev, action, _ = parents[key]
                moves.append(action)
                key = prev
                states.append(parents[key][2])
            moves.reverse()
            states.reverse()
            return moves, states, expanded, len(parents), perf_counter()-start_time
        for next_state, move in successors(p, state):
            next_key = canonical_key(p, next_state)
            if next_key not in parents:
                parents[next_key] = (key, move, next_state)
                frontier.append(next_key)
                if len(parents) >= max_states:
                    raise RuntimeError(f'State cap {max_states} reached')
    return None, None, expanded, len(parents), perf_counter()-start_time


def render(p: Problem, state: tuple[int, ...]) -> str:
    cells = occupancy(p, state)
    lines = []
    for r in range(p.rows):
        lines.append(' '.join('.' if cells[r*p.cols+c] == -1
                              else p.names[cells[r*p.cols+c]] for c in range(p.cols)))
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generalized Klotski BFS solver')
    parser.add_argument('--problem', choices=[f'p{i:02}' for i in range(1, 7)])
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--show-boards', action='store_true')
    parser.add_argument('--max-states', type=int, default=3_000_000)
    args = parser.parse_args()
    problems = parse_problems(Path(__file__).with_name('klotski_problems.txt'))
    chosen = list(problems.values()) if args.all or not args.problem else [problems[args.problem]]
    for p in chosen:
        moves, states, expanded, discovered, seconds = solve(p, args.max_states)
        print(f'\n{p.name}: {"SOLVED" if moves is not None else "NO SOLUTION"}')
        print(f'Moves: {len(moves) if moves is not None else "-"}; '
              f'expanded: {expanded}; discovered: {discovered}; time: {seconds:.3f}s')
        if moves is not None:
            print('Sequence: ' + ', '.join(f'{name}:{direction}' for name, direction in moves))
            if args.show_boards:
                for step, state in enumerate(states):
                    print(f'\nStep {step}: {"start" if step == 0 else moves[step-1]}\n{render(p, state)}')


if __name__ == '__main__':
    main()
