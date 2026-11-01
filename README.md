*This project has been created as part of the 42 curriculum by vivozzo-.*

# Fly-in


A graph-based drone routing simulator. It reads a map of connected zones, routes a whole fleet of drones from the start zone to the end zone in as few simulation turns as possible, and shows the result both as a turn-by-turn log in the terminal and as an interactive graphical window.

## Table of contents

1. [Description](#description)
2. [Instructions](#instructions)
3. [Map file format](#map-file-format)
4. [Algorithm choices and implementation strategy](#algorithm-choices-and-implementation-strategy)
5. [Visual representation](#visual-representation)
6. [Example input and expected output](#example-input-and-expected-output)
7. [Benchmark results](#benchmark-results)
8. [Project structure](#project-structure)
9. [Technical choices](#technical-choices)
10. [Resources](#resources)

## Description

**Goal.** Given a network of zones (a graph) and a fleet of `nb_drones` drones that all start in the same zone, move every drone to the end zone in the **fewest possible simulation turns**, while respecting every rule of the subject:

- zone capacity (`max_drones`) and connection capacity (`max_link_capacity`);
- movement costs by zone type: `normal` and `priority` cost 1 turn, `restricted` costs 2 turns, `blocked` zones can never be entered;
- a drone moving towards a restricted zone is in flight on the connection for one turn and **must** arrive on the next one (it cannot wait on the link);
- the start and end zones have no capacity limit.

**Overview.** The project is split into four independent, fully object-oriented parts:

| Part | Responsibility |
| --- | --- |
| **Parser** | Reads the map file, validates every line (structure, zone types, capacities, duplicated connections, unknown zones...) and builds the graph. Errors are reported with the line number and the cause. |
| **Solver** | Computes the path and the turn-by-turn timeline of every drone, avoiding conflicts and deadlocks. |
| **Terminal output** | Prints the simulation turn by turn and runs the performance benchmark. |
| **Visual output** | A `pygame` window that replays the simulation with playback controls. |

No graph library is used (no `networkx`, `graphlib`, etc.): the graph, the search and the scheduling are implemented from scratch.

## Instructions

### Requirements

- Python **3.10 or later** (developed with Python 3.12)
- `pygame` (graphical output), `flake8` and `mypy` (linting). The `Makefile` installs all of them in a local virtual environment.

### Installation

```bash
make install
```

This creates a `venv/` directory and installs `pygame`, `flake8` and `mypy` into it.

### Running

All commands must be run **from the root of the repository** (the graphical output loads its fonts and images using paths relative to the root).

```bash
# Terminal output (default map is set by ARGS in the Makefile)
make run ARGS=maps/easy/01_linear_path.txt

# Terminal output + graphical window
make visual ARGS=maps/medium/03_priority_puzzle.txt

# Performance benchmark on all the reference maps
make benchmark
```

Or directly, without `make`:

```bash
python3 source/main.py <map_file> [--visual_output | --benchmark]
```

| Flag | Effect |
| --- | --- |
| *(none)* | Prints the simulation in the terminal. |
| `--visual_output` | Prints the simulation in the terminal and opens the graphical window. |
| `--benchmark` | Solves every reference map in `maps/`, prints a Target / Achieved / Status table and saves all the simulations in `benchmark_output.txt`. |

### Makefile rules

| Rule | Description |
| --- | --- |
| `install` | Creates the virtual environment and installs the dependencies. |
| `run` | Runs the simulation with terminal output. |
| `visual` | Runs the simulation with terminal and graphical output. |
| `benchmark` | Runs the performance benchmark. |
| `debug` | Runs the program under `pdb`. |
| `lint` | Runs `flake8` and `mypy` with the flags required by the subject. |
| `lint-strict` | Runs `flake8` and `mypy --strict`. |
| `clean` | Removes `__pycache__`, `.mypy_cache` and `.pyc` files. |
| `fclean` | `clean` + removes the virtual environment. |
| `re` | `fclean` + `all`. |

### Error handling

The program never crashes on a bad input: every error (wrong usage, missing file, invalid map) is caught and printed as a clear message. For example, a map with an unknown zone type:

```text
Caught the following error(s):
Zone 'lava' at line 3 is not allowed, must be: 'normal', 'blocked', 'restricted' or 'priority'
```

## Map file format

```text
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: corridorA-tunnelB [max_link_capacity=2]
# comments start with '#'
```

- `nb_drones: <positive_integer>` must be the first line.
- Exactly one `start_hub` and one `end_hub`; every zone has a unique name (no dashes or spaces) and integer coordinates.
- Optional zone metadata: `zone=<normal|blocked|restricted|priority>` (default `normal`), `color=<single word>`, `max_drones=<positive integer>` (default 1, ignored on the start and end zones).
- Connections are bidirectional, only link previously defined zones, cannot be duplicated (`a-b` and `b-a` are the same) and accept `max_link_capacity=<positive integer>` (default 1).

The reference maps are in `maps/easy`, `maps/medium`, `maps/hard` and `maps/challenger`.

## Algorithm choices and implementation strategy

### Overview: sequential, time-aware routing

The solver (`source/solver/algorithm.py`) routes the drones **one at a time**. For each drone it runs a shortest-path search that already knows what the previous drones have reserved, then it stores the new drone's timeline in the same reservation tables. The next drone therefore "sees" the traffic created by the earlier ones and automatically takes a different route, or waits, when the best route is congested.

```text
for each drone:
    1. reset the distances (start = 0, everything else unknown)
    2. run the time-aware Dijkstra search          -> best path
    3. walk the path turn by turn, inserting waits  -> drone timeline
    4. reserve the timeline in the occupancy tables -> next drones see it
```

### Step 1 - Graph and blocked zones

The parser builds an adjacency list (`graph`) in which **blocked zones are removed**, as well as zones that cannot be reached. No path can ever use a blocked zone, which satisfies the "any path using it is invalid" rule by construction.

### Step 2 - Dijkstra variant measured in turns

The distance used by the search is the **number of turns**, not the number of hops:

- moving into a `normal` or `priority` zone adds 1 turn;
- moving into a `restricted` zone adds 2 turns.

When a neighbour is relaxed, the arrival turn is not simply `distance + cost`. The search checks the reservation tables and **delays the arrival** (`find_total_wait`) while:

1. the connection is already full at that turn (`max_link_capacity`), or
2. the destination zone is already full at that turn (`max_drones`; the end zone has no limit).

This is how strategic waiting is built directly into the path cost: a longer free route can beat a shorter congested one, which spreads the drones across the available paths without any explicit "path distribution" step.

**Priority zones.** When two routes arrive at the same turn, the tie is broken in favour of the one that crosses **more priority zones** (`find_total_priority_zones`). The next zone to visit is also chosen in favour of priority zones when distances are equal. Priority zones never make a route longer, they only decide between equally fast alternatives, as the subject asks.

### Step 3 - Building the timeline

`create_drone_turns` follows the chosen path and writes where the drone is at every turn:

- if the next move is not possible at the earliest turn, the drone **waits** in its current zone (its name is repeated in the timeline) until the connection and the destination have room;
- for a restricted zone the timeline contains the connection name (`zone1-zone2`) for the turn in flight, followed by the destination zone on the next turn. The drone never waits on the link: the check is made **before** it leaves, using the arrival turn.

### Step 4 - Reserving the turns

`update_hubs_connec_occupancy` writes the timeline into two tables:

- `Hub.occupancy_per_turn[turn]` - the `(connection, drone)` pairs present in each zone at each turn (the connection is the one used to arrive, which is what allows counting link usage);
- `Connection.occupancy_per_turn[turn]` - the drones in flight on a link (restricted zones only, because those are the only moves that spend a full turn on the link).

Capacities are checked per turn against these tables, so several drones can move at the same time as long as every zone and connection limit is respected at each turn.

### Limits and trade-offs

Scheduling drones one at a time is a **greedy** strategy: each drone gets the best route available *given the earlier drones*, which is not guaranteed to be the global optimum for every possible map. In exchange it is simple to reason about, avoids conflicts and deadlocks by construction (a drone only moves when the move is already known to be valid at that turn), and, as the benchmark below shows, reaches results well under every reference target - including the challenger map.

## Visual representation

The graphical output (`--visual_output`) is a `pygame` window that replays the simulation. It was designed to make the capacity rules and the routing decisions easy to see.

**What is drawn**

- **Zones** with the color given in the map (gray if the color is not a valid color name), and a **shape per zone type** so the type is readable even without the legend: square = normal, triangle = restricted, diamond = priority, circle = blocked.
- **START / END counters** showing how many drones are in the start zone and how many were already delivered to the end zone at the current turn.
- **Connections** with their `max_link_capacity` written on top, so bottlenecks are visible at a glance.
- **Drones** drawn with their `D<ID>`; drones in flight towards a restricted zone are drawn on the connection.
- **A grid aligned with the map coordinates**, which moves together with the camera.
- A header with the **current turn / total turns**, the map file name, the playback mode and the speed.

**Interaction**

| Input | Action |
| --- | --- |
| `SPACE` | Play / pause (in step mode: next turn) |
| `R` | Reverse the playback |
| `LEFT SHIFT` | Reset to the initial state |
| `M` | Switch between **AUTO** and **STEP** mode |
| `V` / `D` | Increase / decrease the speed (x1 to x8) |
| `H` | Hide / show the controls and the zone legend |
| `ESC` | Exit |
| Mouse drag | Move the map (camera) |
| Mouse hover on a zone | Tooltip with the zone name, type, drones currently inside and occupancy (`current/max_drones`) |

**How it helps.** Playing the simulation forward and backward, one turn at a time, makes it easy to check that capacities are respected, to see where drones wait and why, and to compare routes between maps. The tooltip exposes the exact state of any zone without cluttering the screen, and the shapes plus the legend keep the map readable on any map without relying on color alone.

The terminal output is a plain-text turn log (see below), which is also what the benchmark saves to `benchmark_output.txt`.

## Example input and expected output

### Example 1 - `maps/easy/02_simple_fork.txt`

```text
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: path_a 2 1 [color=blue]
hub: path_b 2 -1 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-junction [max_link_capacity=2]
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

```bash
make run ARGS=maps/easy/02_simple_fork.txt
```

```text
FLY-IN SIMULATION

Map file: 02_simple_fork.txt

1 TURN: D1-junction D2-junction
2 TURN: D1-path_a D2-path_b D3-junction D4-junction
3 TURN: D1-goal D2-goal D3-path_a D4-path_b
4 TURN: D3-goal D4-goal

Total turns: 4
```

Two drones per turn can enter the junction (`max_drones=2` and `max_link_capacity=2`), and they split between `path_a` and `path_b`.

### Example 2 - `maps/medium/03_priority_puzzle.txt` (restricted zone)

```text
nb_drones: 5

start_hub: start 0 0 [color=green]
hub: slow_path1 1 -1 [zone=restricted color=red]
hub: slow_path2 2 -1 [color=red]
hub: fast_junction 1 0 [zone=priority color=blue max_drones=2]
hub: fast_path 2 0 [zone=priority color=blue]
hub: merge_point 3 0 [color=yellow max_drones=3]
end_hub: goal 4 0 [color=green]

connection: start-slow_path1
connection: start-fast_junction
connection: slow_path1-slow_path2
connection: slow_path2-merge_point
connection: fast_junction-fast_path
connection: fast_path-merge_point
connection: merge_point-goal [max_link_capacity=2]
```

```text
FLY-IN SIMULATION

Map file: 03_priority_puzzle.txt

1 TURN: D1-fast_junction D3-start-slow_path1
2 TURN: D1-fast_path D2-fast_junction D3-slow_path1 D5-start-slow_path1
3 TURN: D1-merge_point D2-fast_path D3-slow_path2 D4-fast_junction D5-slow_path1
4 TURN: D1-goal D2-merge_point D3-merge_point D4-fast_path D5-slow_path2
5 TURN: D2-goal D3-goal D4-merge_point D5-merge_point
6 TURN: D4-goal D5-goal

Total turns: 6
```

How to read it:

- Each line is one turn, prefixed with the turn number, and lists only the drones that moved in that turn (waiting drones are omitted, and delivered drones are no longer tracked).
- `D3-start-slow_path1` means D3 is **in flight** on the connection `start-slow_path1` towards a restricted zone; on the next turn it appears in `slow_path1`.
- Most drones use the priority route; D3 and D5 take the restricted route in parallel because it still arrives in time.

## Benchmark results

Results of `make benchmark` (the **Target** column comes from the performance benchmarks of the subject; lower **Achieved** is better):

```text
==========================================================
                  PERFORMANCE BENCHMARK
==========================================================
Map                           Target    Achieved    Status
==========================================================
Easy maps
----------------------------------------------------------
  01_linear_path                   6           4      Pass
  02_simple_fork                   8           4      Pass
  03_basic_capacity                6           4      Pass
----------------------------------------------------------
Medium maps
----------------------------------------------------------
  01_dead_end_trap                12           8      Pass
  02_circular_loop                15          10      Pass
  03_priority_puzzle              12           6      Pass
----------------------------------------------------------
Hard maps
----------------------------------------------------------
  01_maze_nightmare               30          13      Pass
  02_capacity_hell                35          16      Pass
  03_ultimate_challenge           45          26      Pass
----------------------------------------------------------
Challenger map
----------------------------------------------------------
  01_the_impossible_dream         45          43      Pass
----------------------------------------------------------
```

| Difficulty | Map | Drones | Target (turns) | Achieved (turns) | Status |
| --- | --- | :-: | :-: | :-: | :-: |
| Easy | `01_linear_path` | 2 | 6 | **4** | Pass |
| Easy | `02_simple_fork` | 4 | 8 | **4** | Pass |
| Easy | `03_basic_capacity` | 4 | 6 | **4** | Pass |
| Medium | `01_dead_end_trap` | 5 | 12 | **8** | Pass |
| Medium | `02_circular_loop` | 6 | 15 | **10** | Pass |
| Medium | `03_priority_puzzle` | 5 | 12 | **6** | Pass |
| Hard | `01_maze_nightmare` | 8 | 30 | **13** | Pass |
| Hard | `02_capacity_hell` | 12 | 35 | **16** | Pass |
| Hard | `03_ultimate_challenge` | 15 | 45 | **26** | Pass |
| Challenger | `01_the_impossible_dream` | 25 | 45 | **43** | Pass |

Every map meets its target, and **The Impossible Dream beats the reference record of 45 turns, finishing in 43 turns**.

## Project structure

```text
.
├── Makefile
├── README.md
├── maps/                     # reference maps (easy / medium / hard / challenger)
└── source/
    ├── main.py               # entry point and command line handling
    ├── building/
    │   └── models.py         # Hub, Connection and Drone classes
    ├── parser/
    │   └── parsing.py        # Parser: reads and validates the map file
    ├── solver/
    │   └── algorithm.py      # Solver: pathfinding and turn scheduling
    └── visual/
        ├── terminal.py       # TerminalOutput: turn log and benchmark
        ├── visual.py         # VisualOutput: pygame window, Camera, Tooltip
        └── files/            # font and drone image used by the window
```

## Technical choices

- **Completely object-oriented:** `Hub`, `Connection` and `Drone` model the problem; `Parser`, `Solver`, `TerminalOutput` and `VisualOutput` each own one responsibility and communicate only through these models.
- **Completely type-safe:** all functions, parameters, return values and attributes are annotated; the code is checked with `mypy` using the flags required by the subject (`make lint`), and `make lint-strict` runs it with `--strict`.
- **`flake8` compliant** code, with PEP 257 docstrings (Google style) on every module, class and function.
- **No graph libraries:** the graph structure, the shortest-path search and the scheduling are written by hand.
- **Error handling:** parsing problems are accumulated and reported together with their line numbers; any unexpected error is caught in `main` and printed instead of crashing.
- **Resource management:** files are always opened through context managers.

## Resources

### References

- Python documentation: https://docs.python.org/3/
- `typing` module: https://docs.python.org/3/library/typing.html
- PEP 257 (docstring conventions): https://peps.python.org/pep-0257/
- `pygame` documentation: https://www.pygame.org/docs/
- Dijkstra's algorithm (Wikipedia): https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

### How AI was used

AI tools were used as a **learning and review aid**, not as a code generator.

- **Learning concepts:** to understand the ideas behind the project, such as how Dijkstra's algorithm works, how to take waiting time and capacities into account in a shortest-path search, and how reservation tables are used to schedule several agents without conflicts.
- **Code review:** to review the code I had already written, point out possible bugs and edge cases, and suggest improvements to readability, docstrings and type hints, which I then checked, tested and applied myself.
- **README:** to help structure and organize this README. The technical content was checked against the actual code and the real program output.

No part of the final solution was copied from an AI tool without being understood first.
