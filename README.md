# Lab 4 — Generalized Klotski

This solution reads the six benchmark boards from `klotski_problems.txt` and searches for a sequence of **single-cell slides** that moves the target piece A to the bottom exit.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python solver.py --all
python solver.py --problem p04
python solver.py --problem p02 --show-boards
```

## Method

- **State:** a tuple of the top-left cell offsets of the rectangular pieces, in a fixed piece order. Shapes are parsed from the input.
- **Actions:** move any whole piece one cell up, down, left, or right, provided it remains inside the board and does not overlap another piece.
- **Goal:** the target A reaches the last row and spans precisely the exit columns. "Reaches exit" is treated as **covers the exit**, as stated in the repository.
- **Search:** breadth-first search (FIFO queue) with a visited set. Since each edge is a one-cell slide, BFS minimizes the number of slides.
- **Duplicate elimination:** within the visited keys, positions of non-target pieces with identical rectangular dimensions are sorted. Such pieces are interchangeable for goal reachability, reducing the explored state space. Their labels are retained in the concrete path for readable move output.
- **Output:** move sequence, explored/expanded states, discovered canonical states, wall-clock time.

## Observed results

| Puzzle | Status | Optimal slides | Expanded states | Discovered states |
|---|---|---:|---:|---:|
| p01 | solved | 8 | 113 | 144 |
| p02 | solved | 18 | 252 | 263 |
| p03 | solved | 45 | 2141 | 2153 |
| p04 | solved | 116 | 24009 | 24084 |
| p05 | solved | 179 | 40087 | 40600 |
| p06 | no solution under stated rules | — | 833 | 833 |

`p06` is genuinely unreachable **under the one-cell orthogonal slide rules and exit in columns 1,2**. We additionally confirmed this using a second exhaustive BFS that keeps all labels distinct: it inspected **39,984** reachable labeled states and found no goal. This may be an intentional unsolvable benchmark or an error in the provided configuration; confirm with the instructor before changing its board.

The expanded/discovered counts depend on successor order and duplicate handling. Times differ by computer; the included `results.txt` contains timings from one run.

## Source

Initial layouts from https://github.com/GiuseppeEsposito98/Lab4-exercises/blob/main/klotski_problems.txt

## Optional improvements

Compare BFS against A* with an admissible target-distance heuristic, or add an animation or move-by-move trace.
