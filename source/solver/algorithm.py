# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   algorithm.py                                        :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/21 10:58:09 by vivozzo-           #+#    #+#             #
#   Updated: 2026/11/02 12:11:57 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

from building import Hub, Connection, Drone
from typing import NamedTuple


class DistInfo(NamedTuple):
    """Best known way to reach a hub in the shortest path search.

    Attributes:
        distance: Turns needed to reach the hub (``None`` if unknown).
        previous: Hub visited just before it (``None`` for the start).
    """

    distance: int | None
    previous: Hub | None


class Solver:
    """Compute the path and the turn-by-turn moves of every drone.

    Drones are scheduled one at a time. For each one, a Dijkstra-like
    search finds the fastest path taking into account the turns already
    reserved by the previous drones (zone and connection capacities,
    waiting turns, restricted and priority zones). The resulting timeline
    is then stored in the occupancy tables, so the next drones avoid
    conflicts and are spread over different routes when needed.

    Attributes:
        nb_drones: Number of drones to route.
        list_hub: Regular hubs (without the start and end hubs).
        list_connection: All the connections of the map.
        start_hub: Starting zone.
        end_hub: Target zone.
        dist_hubs: Best known ``DistInfo`` of each hub during the search.
        list_drones: Drones created by ``create_drones``.
        graph: Adjacency list of the usable zones.
    """

    def __init__(self, nb_drones: int, list_hub: list[Hub],
                 list_connection: list[Connection],
                 start_hub: Hub, end_hub: Hub, graph: dict[str, list[str]]
                 ) -> None:
        """Create the solver.

        Args:
            nb_drones: Number of drones to route.
            list_hub: Regular hubs (without the start and end hubs).
            list_connection: All the connections of the map.
            start_hub: Starting zone.
            end_hub: Target zone.
            graph: Adjacency list of the usable zones.
        """

        self.nb_drones = nb_drones
        self.list_hub = list_hub
        self.list_connection = list_connection
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.dist_hubs: dict[Hub, DistInfo] = {}
        self.list_drones: list[Drone] = []
        self.graph: dict[str, list[str]] = graph

    def create_drones(self, nb_drones: int) -> None:
        """Create the drones and add them to ``list_drones``.

        Args:
            nb_drones: Number of drones to create (ids start at 1).
        """

        for i in range(nb_drones):
            drone = Drone(i+1)
            self.list_drones.append(drone)

    def create_path(self) -> list[str]:
        """Rebuild the path found by the search.

        Goes from the end hub back to the start hub following the
        ``previous`` links of ``dist_hubs``.

        Returns:
            Zone names from the start hub to the end hub.

        Raises:
            ValueError: If a hub has no previous hub, meaning there is no
                valid path.
        """

        current_hub = self.end_hub
        path = []

        while current_hub != self.start_hub:
            path.append(current_hub.name)
            previous_hub = self.dist_hubs[current_hub].previous
            if previous_hub is None:
                raise ValueError(
                    "Algorithm failed trying to find a valid path")
            current_hub = previous_hub

        path.append(self.start_hub.name)
        path.reverse()

        return path

    def find_connection(self, first_name: str,
                        second_name: str) -> Connection | None:
        """Find the connection between two zones, in any direction.

        Args:
            first_name: Name of one zone.
            second_name: Name of the other zone.

        Returns:
            The connection, or ``None`` if the zones are not connected.
        """

        for connection in self.list_connection:
            if ((connection.first_name == first_name and
                 connection.second_name == second_name) or
                    (connection.first_name == second_name and
                     connection.second_name == first_name)):
                return connection
        return None

    def find_hub(self, hub_name: str) -> Hub:
        """Find a hub by its name.

        Args:
            hub_name: Name of the hub (including start and end hubs).

        Returns:
            The matching hub.

        Raises:
            ValueError: If there is no hub with that name.
        """

        for hb in self.list_hub:
            if hb.name == hub_name:
                return hb
        if hub_name == self.start_hub.name:
            return self.start_hub
        if hub_name == self.end_hub.name:
            return self.end_hub

        raise ValueError(f"Hub '{hub_name}' not found")

    def find_total_priority_zones(self, hub: Hub) -> int:
        """Count the priority zones on the best path to a hub.

        Follows the ``previous`` links of ``dist_hubs`` back to the start.
        Used to break ties between paths with the same number of turns,
        preferring the one that crosses more priority zones.

        Args:
            hub: Hub at the end of the path.

        Returns:
            Number of priority zones found, including ``hub`` itself.

        Raises:
            ValueError: If the chain of previous hubs is broken.
        """

        count = 0
        current_hub = hub

        if hub.zone_type == "priority":
            count += 1

        while current_hub != self.start_hub:
            previous_hub = self.dist_hubs[current_hub].previous
            if previous_hub is None:
                raise ValueError(
                    "Algorithm failed trying to find a valid path")
            if previous_hub.zone_type == "priority":
                count += 1
            current_hub = previous_hub

        return count

    def check_turns_if_priority(self, hub: Hub) -> int:
        """Tell whether a hub counts as a priority zone.

        Args:
            hub: Hub to check.

        Returns:
            1 if the hub is a priority zone, otherwise 0.
        """

        if hub.zone_type == "priority":
            return 1
        return 0

    def check_connection(self, hub_visited: Hub,
                         hub_connection: Hub, turn: int) -> bool:
        """Check if a connection can take one more drone.

        Counts the drones already using the link (in flight and
        arriving through it) around the given turn and compares with
        ``max_link_capacity``.

        Args:
            hub_visited: Hub where the move starts.
            hub_connection: Destination hub of the move.
            turn: Turn in which the drone arrives at ``hub_connection``.

        Returns:
            True if the link has room for one more drone, False otherwise.
            A negative ``turn`` is always accepted.

        Raises:
            ValueError: If the two hubs are not connected.
        """

        connection = self.find_connection(
            hub_visited.name, hub_connection.name)
        if connection is None:
            raise ValueError("Algorithm failed trying to find a valid path")

        if turn < 0:
            return True

        count_total_connec = 0

        # if it is restricted, we will only check the connection occupancy,
        # because if it is not restricted,
        # the update will save the connec itself and not the connec occupancy
        # (the drone doesnt stay 1 turn in the connection)
        # restricted will save the connection in the hub occupancy and will
        # increase the connection occupancy, so this
        # would cause the count to be duplicated
        if hub_connection.zone_type != "restricted":
            if turn < len(hub_connection.occupancy_per_turn):
                for connec in hub_connection.occupancy_per_turn[turn]:
                    if connec[0] == connection:
                        count_total_connec += 1
            if turn < len(hub_visited.occupancy_per_turn):
                for connec in hub_visited.occupancy_per_turn[turn]:
                    if connec[0] == connection:
                        count_total_connec += 1
        else:
            # restricted destination: the drone is on the connection during
            # turn - 1, so also count drones arriving in hub_visited at that
            # turn through this same connection (opposite direction)
            if 0 <= turn - 1 < len(hub_visited.occupancy_per_turn):
                for connec in hub_visited.occupancy_per_turn[turn - 1]:
                    if connec[0] == connection:
                        count_total_connec += 1

        if 0 <= turn - 1 < len(connection.occupancy_per_turn):
            count_total_connec += len(connection.occupancy_per_turn[turn - 1])

        if (count_total_connec + 1 > connection.max_link_capacity):
            return False

        return True

    def update_hubs_connec_occupancy(self, drone: Drone) -> None:
        """Reserve the turns of a drone in the occupancy tables.

        For every turn of ``drone.turns``: if the drone is in flight on a
        connection, it is added to ``connection.occupancy_per_turn``;
        otherwise it is added to ``hub.occupancy_per_turn`` together with the
        connection used to arrive (an empty one when the drone just waited).
        The start hub is ignored.

        Args:
            drone: Drone with its ``turns`` already computed.

        Raises:
            ValueError: If a connection used by the drone does not exist.
        """

        # empty connection used when a drone is only waiting in a hub
        empty_connec = Connection("", "", 1)
        for index, name in enumerate(drone.turns):
            if name == self.start_hub.name:
                continue
            if "-" in name:
                first_name, second_name = name.split("-")
                connection = self.find_connection(first_name, second_name)
                if connection is None:
                    raise ValueError("no connection")
                while len(connection.occupancy_per_turn) <= index:
                    connection.occupancy_per_turn.append([])
                connection.occupancy_per_turn[index].append(drone)
                continue
            hub = self.find_hub(name)
            connec = empty_connec
            if name != drone.turns[index - 1]:
                # the previous hub is turns[index - 1], unless the drone was
                # in flight on a connection (restricted): then it is
                # turns[index - 2]
                prev_name = drone.turns[index - 1]
                if "-" in prev_name:
                    prev_name = drone.turns[index - 2]
                found_connec = self.find_connection(name, prev_name)
                if found_connec is None:
                    raise ValueError("Algorithm failed trying to find a "
                                     "valid path")
                connec = found_connec
            while len(hub.occupancy_per_turn) <= index:
                hub.occupancy_per_turn.append([])
            hub.occupancy_per_turn[index].append((connec, drone))

    def find_shortest_path(self) -> bool:
        """Find the fastest path from the start to the end hub.

        Dijkstra variant where the distance is measured in turns. When
        relaxing a neighbour, the cost of the zone type (1 for normal and
        priority, 2 for restricted) is added and the move is delayed while the
        connection or the destination hub is full, according to the turns
        reserved by the previous drones. Ties are broken in favor of paths
        with more priority zones. Results are stored in ``dist_hubs``.

        Returns:
            True if the search finished, False if it got stuck because no
            reachable hub was left to visit.

        Raises:
            ValueError: If the graph and the connections are inconsistent.
        """

        turn_cost_zone = {"normal": 1, "restricted": 2, "priority": 1}
        connections: list[str] = []
        visited_hubs: list[str] = []

        def find_total_wait(turn: int, hub_connection: Hub,
                            hub_visited: Hub) -> int:
            """Find the first turn in which a move is possible.

            Starting at ``turn``, keeps adding turns while the connection
            has no free capacity and then while the destination hub is
            full (the end hub has no limit).

            Args:
                turn: Earliest turn in which the drone would arrive.
                hub_connection: Destination hub.
                hub_visited: Hub where the move starts.

            Returns:
                The turn in which the drone can arrive at ``hub_connection``.

            Raises:
                ValueError: If the two hubs are not connected.
            """

            connection = self.find_connection(
                hub_visited.name, hub_connection.name)
            if connection is None:
                raise ValueError(
                    "Algorithm failed trying to find a valid path")

            # connection:
            while True:
                count_total_connec = 0
                if hub_connection.zone_type != "restricted":
                    if turn < len(hub_connection.occupancy_per_turn):
                        for connec in hub_connection.occupancy_per_turn[turn]:
                            if connec[0] == connection:
                                count_total_connec += 1
                    if turn < len(hub_visited.occupancy_per_turn):
                        for connec in hub_visited.occupancy_per_turn[turn]:
                            if connec[0] == connection:
                                count_total_connec += 1
                else:
                    # restricted destination: the drone is on
                    # the connection during
                    # turn - 1, so also count drones
                    # arriving in hub_visited at that
                    # turn through this same connection (opposite direction)
                    if 0 <= turn - 1 < len(hub_visited.occupancy_per_turn):
                        for connec in hub_visited.occupancy_per_turn[turn - 1]:
                            if connec[0] == connection:
                                count_total_connec += 1

                if 0 <= turn - 1 < len(connection.occupancy_per_turn):
                    count_total_connec += len(
                        connection.occupancy_per_turn[turn - 1])

                if (count_total_connec + 1 > connection.max_link_capacity):
                    turn += 1
                    continue
                break

            # hub:
            while hub_connection != self.end_hub:
                if ((turn < len(hub_connection.occupancy_per_turn)) and
                    (len(hub_connection.occupancy_per_turn[
                        turn]) + 1 >
                        hub_connection.max_drones)):
                    turn += 1
                    continue
                break

            return turn

        while len(visited_hubs) != len(self.dist_hubs):

            next_hub_visited = None
            if len(visited_hubs) == 0:
                hub_visited = self.start_hub
            connections = self.graph[hub_visited.name]
            turns_visited = self.dist_hubs[hub_visited].distance
            if turns_visited is None:
                raise ValueError("Algorithm failed trying to "
                                 "find a valid path")
            for hub_name in connections:
                if hub_name in visited_hubs:
                    continue

                hub_connection = self.find_hub(hub_name)
                turns_visited_connect = turn_cost_zone[
                    hub_connection.zone_type]
                turns_start_connect = (find_total_wait(
                    turns_visited + turns_visited_connect,
                    hub_connection,
                    hub_visited))
                connection_dist = self.dist_hubs[hub_connection].distance

                if (connection_dist is None or
                    connection_dist > turns_start_connect
                    or (connection_dist == turns_start_connect
                        and self.find_total_priority_zones(hub_visited) +
                        self.check_turns_if_priority(hub_connection) >
                        self.find_total_priority_zones(hub_connection))):

                    if (len(hub_connection.occupancy_per_turn) - 1 <
                        turns_start_connect or
                        (hub_connection != self.end_hub and
                            self.check_connection(hub_visited,
                                                  hub_connection,
                                                  turns_start_connect) and
                            (len(hub_connection.occupancy_per_turn[
                                turns_start_connect]) + 1 <=
                                hub_connection.max_drones))):
                        self.dist_hubs[hub_connection] = DistInfo(
                            turns_start_connect, hub_visited)
                    elif (hub_connection == self.end_hub and
                            self.check_connection(hub_visited,
                                                  hub_connection,
                                                  turns_start_connect)):
                        self.dist_hubs[hub_connection] = DistInfo(
                            turns_start_connect, hub_visited)

            smallest_turns_start_connect: int | None = None
            for hub in self.dist_hubs:
                hub_distance = self.dist_hubs[hub].distance
                if (hub.name not in visited_hubs and
                    hub_distance is not None and
                    (smallest_turns_start_connect is None or
                     hub_distance < smallest_turns_start_connect or
                     (hub_distance == smallest_turns_start_connect and
                      hub.zone_type == "priority"))):
                    smallest_turns_start_connect = hub_distance
                    next_hub_visited = hub

            if hub_visited.name not in visited_hubs:
                visited_hubs.append(hub_visited.name)

            if next_hub_visited is None:
                return False
            hub_visited = next_hub_visited

        return True

    def clean_dist_hubs(self) -> None:
        """Reset ``dist_hubs`` before searching a path for a drone.

        The start hub gets distance 0 and every other usable hub gets an
        unknown distance and no previous hub. Blocked and unreachable hubs
        are left out.
        """

        self.dist_hubs[self.start_hub] = DistInfo(0, None)
        for hub in list(self.list_hub):
            if hub.zone_type != "blocked" and hub.name in self.graph:
                self.dist_hubs[hub] = DistInfo(None, None)
        self.dist_hubs[self.end_hub] = DistInfo(None, None)

    def create_drone_turns(self, drone: Drone) -> None:
        """Build the turn-by-turn timeline of a drone.

        Follows ``drone.path``. For each step the drone waits in the current
        hub (its name is repeated in the timeline) until the connection and
        the destination have room at the arrival turn. For a restricted zone
        the connection name ``<zone1>-<zone2>`` is added for the turn the
        drone spends in flight. The result is saved in ``drone.turns``, where
        the index is the turn number and the first item is the start hub.

        Args:
            drone: Drone whose ``path`` was already computed.
        """

        def check_hub(prev: Hub, hub: Hub, turn: int) -> bool:
            """Check if a drone can arrive at a hub at a given turn.

            Args:
                prev: Hub where the move starts.
                hub: Destination hub.
                turn: Turn of arrival at ``hub``.

            Returns:
                True if the connection and the destination have enough capacity
                (the end hub has no limit), False otherwise.
            """

            if not self.check_connection(prev, hub, turn):
                return False
            if hub == self.end_hub:
                return True
            if turn >= len(hub.occupancy_per_turn):
                return True
            return len(hub.occupancy_per_turn[turn]) < hub.max_drones

        turns = [self.start_hub.name]
        for i in range(1, len(drone.path)):
            prev_hub = self.find_hub(drone.path[i - 1])
            hub = self.find_hub(drone.path[i])
            if hub.zone_type == "restricted":
                cost = 2
            else:
                cost = 1
            while not check_hub(prev_hub, hub, len(turns) - 1 + cost):
                turns.append(prev_hub.name)
            if cost == 2:
                connec = self.find_connection(prev_hub.name, hub.name)
                if connec is None:
                    raise ValueError("Algorithm failed trying to find a "
                                     "valid path")
                turns.append(f"{connec.first_name}-{connec.second_name}")
            turns.append(hub.name)
        drone.turns = turns

    def find_path(self) -> None:
        """Compute the path and the timeline of every drone.

        Creates the drones and, for each one, searches the shortest path
        with the current occupancy, creates its turns and reserves them so
        that the following drones avoid it.

        Raises:
            ValueError: If no valid path can be found.
        """

        self.create_drones(self.nb_drones)

        for i in range(self.nb_drones):

            self.clean_dist_hubs()

            if not self.find_shortest_path():
                raise ValueError(
                    "Algorithm failed trying to find a valid path")

            path = self.create_path()

            self.list_drones[i].path = path

            self.create_drone_turns(self.list_drones[i])

            self.update_hubs_connec_occupancy(self.list_drones[i])
