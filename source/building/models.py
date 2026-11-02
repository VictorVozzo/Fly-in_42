# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   models.py                                           :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/22 11:21:45 by vivozzo-           #+#    #+#             #
#   Updated: 2026/11/02 12:09:12 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

class Hub:
    """Zone (node) of the drone network.

    Attributes:
        name: Unique zone name.
        first_coord: X coordinate of the zone.
        second_coord: Y coordinate of the zone.
        zone_type: One of ``normal``, ``blocked``, ``restricted`` or
            ``priority``.
        color: Color name used by the visual output (``none`` if unset).
        max_drones: Maximum number of drones allowed in the zone at once.
        occupancy_per_turn: For each turn (list index), the
            ``(Connection, Drone)`` pairs present in the zone. The
            connection is the one used to arrive (an empty connection
            when the drone was only waiting).
    """

    def __init__(self, name: str, first_coord: int, second_coord: int,
                 zone_type: str, color: str, max_drones: int) -> None:
        """Create a zone.

        Args:
            name: Unique zone name.
            first_coord: X coordinate of the zone.
            second_coord: Y coordinate of the zone.
            zone_type: Zone type (``normal``, ``blocked``, ``restricted`` or
                ``priority``).
            color: Color name used for the visual representation.
            max_drones: Maximum number of drones that can occupy the zone.
        """

        self.name = name
        self.first_coord = first_coord
        self.second_coord = second_coord
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.occupancy_per_turn: list[list[tuple[Connection, Drone]]] = []


class Connection:
    """Bidirectional link between two zones.

    Attributes:
        first_name: Name of the first zone.
        second_name: Name of the second zone.
        max_link_capacity: Maximum number of drones that can traverse the
            link simultaneously.
        occupancy_per_turn: For each turn (list index), the drones that
            are in flight on this link.
    """

    def __init__(self, first_name: str, second_name: str,
                 max_link_capacity: int) -> None:
        """Create a connection between two zones.

        Args:
            first_name: Name of the first zone.
            second_name: Name of the second zone.
            max_link_capacity: Maximum number of drones that can traverse
                the link simultaneously.
        """

        self.first_name = first_name
        self.second_name = second_name
        self.max_link_capacity = max_link_capacity
        self.occupancy_per_turn: list[list[Drone]] = []


class Drone:
    """Drone that must travel from the start zone to the end zone.

    Attributes:
        id: Drone identifier (starts at 1, displayed as ``D<id>``).
        path: Ordered names of the zones the drone goes through.
        turns: Position of the drone at each turn (list index). Each item
            is a zone name, or ``<zone1>-<zone2>`` while the drone is in
            flight towards a restricted zone.
    """

    def __init__(self, id: int) -> None:
        """Create a drone with an empty path and timeline.

        Args:
            id: Drone identifier.
        """

        self.id = id
        self.path: list[str] = []
        self.turns: list[str] = []
