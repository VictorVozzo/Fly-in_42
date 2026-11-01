# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   terminal.py                                         :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/17 17:03:18 by vivozzo-           #+#    #+#             #
#   Updated: 2026/10/29 11:20:26 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

from building import Drone, Hub
from parser import Parser
from solver import Solver
from dataclasses import dataclass


@dataclass
class BenchmarkMap:
    """Reference data and result for one benchmark map.

    Attributes:
        target_turns: Maximum number of turns expected for the map.
        path: Path of the map file.
        achieved_turns: Number of turns obtained by the solver.
    """

    target_turns: int
    path: str
    achieved_turns: int = 0


class TerminalOutput:
    """Print the simulation in the terminal and run the benchmark.

    Attributes:
        list_drones: Drones with their timelines already computed.
        start_hub: Starting zone.
        map_file: Name of the map file (without its directory).
    """

    def __init__(self, list_drones: list[Drone], start_hub: Hub,
                 map_file: str) -> None:
        """Create the terminal output.

        Args:
            list_drones: Drones with their timelines already computed.
            start_hub: Starting zone.
            map_file: Path of the map file; only its name is kept.
        """

        self.list_drones = list_drones
        self.start_hub = start_hub
        self.map_file = map_file.split("/")[-1]

    @staticmethod
    def find_total_turns(list_drones: list[Drone]) -> int:
        """Compute the total number of simulation turns.

        Args:
            list_drones: Drones with their timelines already computed.

        Returns:
            The number of turns until the last drone arrives.
        """

        total_turns = 0

        for drone in list_drones:
            if len(drone.turns) - 1 > total_turns:
                total_turns = len(drone.turns) - 1

        return total_turns

    def output(self, list_drones: list[Drone], start_hub: Hub,
               map_file: str) -> str:
        """Build the text of the simulation.

        Each turn is one line, starting with its number, followed by the
        moves ``D<id>-<zone>`` (or ``D<id>-<connection>`` when in flight) of
        the drones that moved in that turn. Drones that stay in place are
        omitted. The map name and the total number of turns are included.

        Args:
            list_drones: Drones with their timelines already computed.
            start_hub: Starting zone.
            map_file: Path or name of the map file.

        Returns:
            The complete simulation text.
        """

        total_turns = self.find_total_turns(list_drones)

        output = f"\nMap file: {map_file.split('/')[-1]}\n"

        for i in range(total_turns + 1):
            if i != 0:
                output += f"{i} TURN: "
            for drone in list_drones:
                if (i != 0 and len(drone.turns) > i and
                    drone.turns[i] != drone.turns[i-1] and
                        drone.turns[i] != start_hub.name):
                    output += f"D{drone.id}-{drone.turns[i]} "
            output += "\n"

        output += f"\nTotal turns: {total_turns}"
        return output

    def print_terminal(self) -> None:
        """Print the simulation in the terminal."""

        print("FLY-IN SIMULATION")
        print(self.output(self.list_drones, self.start_hub, self.map_file))

    def save_output_benchmark_file(self, list_drones: list[Drone],
                                   start_hub: Hub, map_file: str) -> None:
        """Append a simulation to ``benchmark_output.txt``.

        Writes a header if the file is empty and a separator after the
        simulation text.

        Args:
            list_drones: Drones with their timelines already computed.
            start_hub: Starting zone.
            map_file: Path or name of the map file.
        """

        output = self.output(list_drones, start_hub, map_file)
        flag_empty = False
        with open("benchmark_output.txt", "r") as f:
            if f.read().strip() == "":
                flag_empty = True

        with open("benchmark_output.txt", "a") as f:
            if flag_empty:
                f.write("FLY-IN SIMULATION\n" + "=" * 58)
            f.write(output)
            f.write("\n" + "=" * 58)

    def performance_benchmark(self) -> None:
        """Run the solver on all the reference maps and report the result.

        Each map is parsed and solved, and its simulation is saved in
        ``benchmark_output.txt``. At the end, a table with the target turns,
        the achieved turns and a Pass/Fail status per map (easy, medium, hard
        and challenger) is printed and appended to the same file.
        """

        easy_maps: list[BenchmarkMap] = [
            BenchmarkMap(6, "maps/easy/01_linear_path.txt"),
            BenchmarkMap(8, "maps/easy/02_simple_fork.txt"),
            BenchmarkMap(6, "maps/easy/03_basic_capacity.txt"),
        ]
        medium_maps: list[BenchmarkMap] = [
            BenchmarkMap(12, "maps/medium/01_dead_end_trap.txt"),
            BenchmarkMap(15, "maps/medium/02_circular_loop.txt"),
            BenchmarkMap(12, "maps/medium/03_priority_puzzle.txt"),
        ]
        hard_maps: list[BenchmarkMap] = [
            BenchmarkMap(30, "maps/hard/01_maze_nightmare.txt"),
            BenchmarkMap(35, "maps/hard/02_capacity_hell.txt"),
            BenchmarkMap(45, "maps/hard/03_ultimate_challenge.txt"),
        ]
        challenger_map = BenchmarkMap(
            45, "maps/challenger/01_the_impossible_dream.txt"
        )

        with open("benchmark_output.txt", "w") as f:
            f.write("")

        for easy_map in easy_maps:
            print(f"Parsing the map: {easy_map.path}")
            parsing = Parser()
            final_data = parsing.parsing([str(easy_map.target_turns),
                                          easy_map.path])
            print("Parsing done successfully\n")
            solver = Solver(final_data[0], final_data[1], final_data[2],
                            final_data[3], final_data[4], parsing.graph)
            solver.find_path()
            terminal_output = TerminalOutput(
                solver.list_drones, final_data[3], easy_map.path)
            easy_map.achieved_turns = terminal_output.find_total_turns(
                solver.list_drones)
            self.save_output_benchmark_file(
                solver.list_drones, final_data[3], easy_map.path)

        for medium_map in medium_maps:
            print(f"Parsing the map: {medium_map.path}")
            parsing = Parser()
            final_data = parsing.parsing([str(medium_map.target_turns),
                                          medium_map.path])
            print("Parsing done successfully\n")
            solver = Solver(final_data[0], final_data[1], final_data[2],
                            final_data[3], final_data[4], parsing.graph)
            solver.find_path()
            terminal_output = TerminalOutput(
                solver.list_drones, final_data[3], medium_map.path)
            medium_map.achieved_turns = terminal_output.find_total_turns(
                solver.list_drones)
            self.save_output_benchmark_file(
                solver.list_drones, final_data[3], medium_map.path)

        for hard_map in hard_maps:
            print(f"Parsing the map: {hard_map.path}")
            parsing = Parser()
            final_data = parsing.parsing([str(hard_map.target_turns),
                                          hard_map.path])
            print("Parsing done successfully\n")
            solver = Solver(final_data[0], final_data[1], final_data[2],
                            final_data[3], final_data[4], parsing.graph)
            solver.find_path()
            terminal_output = TerminalOutput(
                solver.list_drones, final_data[3], hard_map.path)
            hard_map.achieved_turns = terminal_output.find_total_turns(
                solver.list_drones)
            self.save_output_benchmark_file(
                solver.list_drones, final_data[3], hard_map.path)

        print(f"Parsing the map: {challenger_map.path}")
        parsing = Parser()
        final_data = parsing.parsing([str(challenger_map.target_turns),
                                      challenger_map.path])
        print("Parsing done successfully\n")
        solver = Solver(final_data[0], final_data[1], final_data[2],
                        final_data[3], final_data[4], parsing.graph)
        solver.find_path()
        terminal_output = TerminalOutput(
            solver.list_drones, final_data[3], challenger_map.path)
        challenger_map.achieved_turns = terminal_output.find_total_turns(
            solver.list_drones)
        self.save_output_benchmark_file(
            solver.list_drones, final_data[3], challenger_map.path)

        w_map, w_target, w_achieved, w_status = 26, 8, 10, 8
        sep = "  "
        total_width = w_map + w_target + w_achieved + w_status + len(sep) * 3

        benchmark_text = ""

        benchmark_text += "\n" + "=" * total_width + "\n"
        benchmark_text += f"{'PERFORMANCE BENCHMARK':^{total_width}}\n"
        benchmark_text += "=" * total_width + "\n"
        benchmark_text += (f"{'Map':<{w_map}}{sep}"
                           + f"{'Target':>{w_target}}{sep}"
                           + f"{'Achieved':>{w_achieved}}{sep}"
                           + f"{'Status':>{w_status}}\n")

        benchmark_text += "=" * total_width + "\n"

        benchmark_text += "Easy maps\n"
        benchmark_text += "-" * total_width + "\n"
        for easy_map in easy_maps:
            map_name = "  " + easy_map.path.split('/')[-1].split('.')[0]
            target = easy_map.target_turns
            achieved = easy_map.achieved_turns
            status = "Pass" if achieved <= target else "Fail"
            benchmark_text += (
                f"{map_name:<{w_map}}{sep}"
                f"{target:>{w_target}}{sep}"
                f"{achieved:>{w_achieved}}{sep}"
                f"{status:>{w_status}}\n"
            )
        benchmark_text += "-" * total_width + "\n"

        benchmark_text += "Medium maps\n"
        benchmark_text += "-" * total_width + "\n"
        for medium_map in medium_maps:
            map_name = "  " + medium_map.path.split('/')[-1].split('.')[0]
            target = medium_map.target_turns
            achieved = medium_map.achieved_turns
            status = "Pass" if achieved <= target else "Fail"
            benchmark_text += (
                f"{map_name:<{w_map}}{sep}"
                f"{target:>{w_target}}{sep}"
                f"{achieved:>{w_achieved}}{sep}"
                f"{status:>{w_status}}\n"
            )
        benchmark_text += "-" * total_width + "\n"

        benchmark_text += "Hard maps\n"
        benchmark_text += "-" * total_width + "\n"
        for hard_map in hard_maps:
            map_name = "  " + hard_map.path.split('/')[-1].split('.')[0]
            target = hard_map.target_turns
            achieved = hard_map.achieved_turns
            status = "Pass" if achieved <= target else "Fail"
            benchmark_text += (
                f"{map_name:<{w_map}}{sep}"
                f"{target:>{w_target}}{sep}"
                f"{achieved:>{w_achieved}}{sep}"
                f"{status:>{w_status}}\n"
            )
        benchmark_text += "-" * total_width + "\n"

        benchmark_text += "Challenger map\n"
        benchmark_text += "-" * total_width + "\n"
        map_name = "  " + challenger_map.path.split('/')[-1].split('.')[0]
        target = challenger_map.target_turns
        achieved = challenger_map.achieved_turns
        status = "Pass" if achieved <= target else "Fail"
        benchmark_text += (
            f"{map_name:<{w_map}}{sep}"
            f"{target:>{w_target}}{sep}"
            f"{achieved:>{w_achieved}}{sep}"
            f"{status:>{w_status}}\n"
        )
        benchmark_text += "-" * total_width + "\n"

        print(benchmark_text)

        benchmark_text = "\n".join(benchmark_text.splitlines()[2:])

        with open("benchmark_output.txt", "a") as f:
            f.write(f"\n{benchmark_text}\n")

        print("Performance benchmark report saved as 'benchmark_output.txt'\n")
