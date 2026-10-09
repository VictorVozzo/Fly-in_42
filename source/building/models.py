# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   models.py                                           :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/22 11:21:45 by vivozzo-           #+#    #+#             #
#   Updated: 2026/09/24 19:35:20 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

class Hub:
    def __init__(self, name: str, first_coord: int, second_coord: int,
                 zone_type: str, color: str, max_drones: int) -> None:
        self.name = name
        self.first_coord = first_coord
        self.second_coord = second_coord
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.occupancy_per_turn: list[list[tuple[Connection, Drone]]] = []


class Connection:
    def __init__(self, first_name: str, second_name: str,
                 max_link_capacity: int) -> None:
        self.first_name = first_name
        self.second_name = second_name
        self.max_link_capacity = max_link_capacity
        self.occupancy_per_turn: list[list[Drone]] = []


class Drone:
    def __init__(self, id: int) -> None:
        self.id = id
        self.path: list[str] = []
        self.turns: list[str] = []
