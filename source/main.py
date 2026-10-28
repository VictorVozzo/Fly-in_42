# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   main.py                                             :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/15 11:24:48 by vivozzo-           #+#    #+#             #
#   Updated: 2026/09/24 18:36:46 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

from parser import Parser
from solver import Solver
from visual import TerminalOutput
from visual import VisualOutput
from sys import argv


def main() -> None:
    try:
        parsing = Parser()
        final_data = parsing.parsing(argv)
        nb_drones, list_hub, list_connection, start_hub, end_hub = (
            final_data[0], final_data[1], final_data[2], final_data[3],
            final_data[4])

        solver = Solver(nb_drones, list_hub, list_connection,
                        start_hub, end_hub, parsing.graph)
        solver.find_path()

        if len(argv) == 3:
            if argv[2] == "--visual_output":
                TerminalOutput(solver.list_drones,
                               start_hub, argv[1]).print_terminal()
                VisualOutput(solver.list_drones, list_hub, list_connection,
                             start_hub, end_hub, argv[1]).visual()
            elif argv[2] == "--benchmark":
                TerminalOutput(solver.list_drones,
                               start_hub, argv[1]).performance_benchmark()
        else:
            TerminalOutput(solver.list_drones,
                           start_hub, argv[1]).print_terminal()
    except Exception as e:
        print(f"Caught the following error(s): \n{e}")


if __name__ == "__main__":
    main()
