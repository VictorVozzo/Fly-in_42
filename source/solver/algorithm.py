# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   algorithm.py                                        :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/21 10:58:09 by vivozzo-           #+#    #+#             #
#   Updated: 2026/09/25 15:39:31 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

from building import Hub, Connection, Drone
from typing import NamedTuple


class DistInfo(NamedTuple):
    distance: int | None
    previous: Hub | None


class Solver:

    def __init__(self, nb_drones: int, list_hub: list[Hub],
                 list_connection: list[Connection],
                 start_hub: Hub, end_hub: Hub, graph: dict[str, list[str]]
                 ) -> None:
        self.nb_drones = nb_drones
        self.list_hub = list_hub
        self.list_connection = list_connection
        self.start_hub = start_hub
        self.end_hub = end_hub
        # dict with the Hub as the keys and a list with int as the dist(turns)
        # and a string as the previous hub(node) name
        self.dist_hubs: dict[Hub, DistInfo] = {}
        self.list_drones: list[Drone] = []
        self.graph: dict[str, list[str]] = graph

    def create_drones(self, nb_drones: int) -> None:
        for i in range(nb_drones):
            drone = Drone(i+1)
            self.list_drones.append(drone)

    def create_path(self) -> list[str]:
        current_hub = self.end_hub
        path = []

        # to find the path in the dijkstra algorithm,
        # we need to start in the end and go in the start direction
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
        for connection in self.list_connection:
            if ((connection.first_name == first_name and
                 connection.second_name == second_name) or
                    (connection.first_name == second_name and
                     connection.second_name == first_name)):
                return connection
        return None

    def find_hub(self, hub_name: str) -> Hub:
        for hb in self.list_hub:
            if hb.name == hub_name:
                return hb
        if hub_name == self.start_hub.name:
            return self.start_hub
        if hub_name == self.end_hub.name:
            return self.end_hub

        raise ValueError(f"Hub '{hub_name}' not found")

    def find_total_priority_zones(self, hub: Hub) -> int:
        count = 0

        current_hub = hub

        if hub.zone_type == "priority":
            count += 1

        while current_hub != self.start_hub:
            previous_hub = self.dist_hubs[current_hub].previous
            if previous_hub is None:
                raise ValueError(
                    "Algorithm failed trying to find a valid path")
            for connection in self.list_connection:
                if ((connection.first_name == current_hub.name and
                     connection.second_name == previous_hub.name) or
                        (connection.second_name == current_hub.name and
                         connection.first_name == previous_hub.name)):
                    if previous_hub.zone_type == "priority":
                        count += 1
                    break
            current_hub = previous_hub

        return count

    def check_turns_if_priority(self, hub: Hub) -> int:
        if hub.zone_type == "priority":
            return 1
        return 0

    # check if the connection exceed the maximum capacity
    def check_connection(self, hub_visited: Hub,
                         hub_connection: Hub, turn: int) -> bool:
        connection = self.find_connection(
            hub_visited.name, hub_connection.name)
        if connection is None:
            raise ValueError("Algorithm failed trying to find a valid path")

        if turn < 0:
            return True

        count_total_connec = 0

        # if it is restricted, we will only check the connection occupancy,
        #  because if it not restricted,
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

    # update the hub and connection with the real occupancy of drones
    def update_hubs_connec_occupancy(self, path: list[str],
                                     turns_ahead: int, drone: Drone) -> None:

        for hub in self.dist_hubs:
            turn_index = turns_ahead
            path_index = 0
            for hub_name in path:
                if self.find_hub(hub_name).zone_type != "restricted":
                    while len(hub.occupancy_per_turn) <= turn_index:
                        hub.occupancy_per_turn.append([])

                    for connec in self.list_connection:
                        while len(connec.occupancy_per_turn) <= turn_index:
                            connec.occupancy_per_turn.append([])

                    if hub_name == hub.name and hub != self.start_hub:
                        connection_found = self.find_connection(
                            hub_name, path[path_index - 1])
                        if connection_found is None:
                            raise ValueError("Algorithm failed trying to "
                                             "find a valid path")
                        hub.occupancy_per_turn[turn_index].append(
                            (connection_found, drone))
                    turn_index += 1
                else:
                    while len(hub.occupancy_per_turn) <= turn_index:
                        hub.occupancy_per_turn.append([])
                    while len(hub.occupancy_per_turn) <= turn_index + 1:
                        hub.occupancy_per_turn.append([])

                    for connection in self.list_connection:
                        while len(connection.occupancy_per_turn) <= turn_index:
                            connection.occupancy_per_turn.append([])
                        while (len(connection.occupancy_per_turn) <=
                                turn_index + 1):
                            connection.occupancy_per_turn.append([])
                        if hub_name == hub.name and hub != self.start_hub:
                            if (((hub_name == connection.first_name and
                                  path[path_index - 1] ==
                                  connection.second_name) or
                                 (hub_name == connection.second_name and
                                  path[path_index - 1] ==
                                  connection.first_name))):
                                connection.occupancy_per_turn[
                                    turn_index].append(drone)

                    if hub_name == hub.name and hub != self.start_hub:
                        cnc = self.find_connection(
                            hub_name, path[path_index - 1])
                        if cnc is None:
                            raise ValueError("Algorithm failed trying to "
                                             "find a valid path")
                        hub.occupancy_per_turn[turn_index +
                                               1].append((cnc, drone))
                    turn_index += 2
                path_index += 1

    # return if it has a path or not
    def find_shortest_path(self, turns_ahead: int) -> bool:
        turn_cost_zone = {"normal": 1, "restricted": 2, "priority": 1}
        connections: list[str] = []
        visited_hubs: list[str] = []

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
                turns_start_connect = turns_visited + turns_visited_connect
                connection_dist = self.dist_hubs[hub_connection].distance

                if (connection_dist is None or
                    connection_dist > turns_start_connect
                    or (connection_dist == turns_start_connect
                        and self.find_total_priority_zones(hub_visited) +
                        self.check_turns_if_priority(hub_connection) >
                        self.find_total_priority_zones(hub_connection))):

                    if (len(hub_connection.occupancy_per_turn) - 1 <
                        turns_start_connect + turns_ahead or
                        (hub_connection != self.end_hub and
                            self.check_connection(hub_visited,
                                                  hub_connection,
                                                  turns_start_connect +
                                                  turns_ahead) and
                            (len(hub_connection.occupancy_per_turn[
                                turns_start_connect + turns_ahead]) + 1 <=
                                hub_connection.max_drones))):
                        self.dist_hubs[hub_connection] = DistInfo(
                            turns_start_connect, hub_visited)
                    elif (hub_connection == self.end_hub and
                            self.check_connection(hub_visited,
                                                  hub_connection,
                                                  turns_start_connect +
                                                  turns_ahead)):
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
        self.dist_hubs[self.start_hub] = DistInfo(0, None)
        for hub in list(self.list_hub):
            if hub.zone_type != "blocked" and hub.name in self.graph:
                self.dist_hubs[hub] = DistInfo(None, None)
        self.dist_hubs[self.end_hub] = DistInfo(None, None)

    def create_drone_turns(self, turns_ahead: int, drone: Drone) -> None:

        drone_path = []
        for i in range(len(drone.path)):
            hub = self.find_hub(drone.path[i])
            if (hub and hub.zone_type == "restricted" and
                    hub.name != self.start_hub.name):
                connection = self.find_connection(
                    drone.path[i-1], drone.path[i])
                if connection is None:
                    raise ValueError("Algorithm failed trying to "
                                     "find a valid path")
                drone_path.append(
                    f"{connection.first_name}-{connection.second_name}")
            drone_path.append(drone.path[i])
        drone.turns = drone_path.copy()

        for _ in range(turns_ahead):
            drone.turns.insert(0, self.start_hub.name)

    def find_total_bottleneck(self) -> int:
        zones_start_names: list[str] = self.graph[self.start_hub.name].copy()
        zones_start: list[Hub] = []

        def check_dead_end(zone_name: str) -> bool:
            queue = [self.start_hub.name]
            visited = [self.start_hub.name]
            while queue:
                current_hub = queue.pop(0)
                if current_hub == self.end_hub.name:
                    return False
                if current_hub == self.start_hub.name:
                    visited.append(zone_name)
                    queue.append(zone_name)
                else:
                    for neighbour in self.graph[current_hub]:
                        if neighbour not in visited:
                            visited.append(neighbour)
                            queue.append(neighbour)
            return True

        valid_zones_names: list[str] = []
        for hub_name in zones_start_names:
            if not check_dead_end(hub_name):
                valid_zones_names.append(hub_name)
        for zone in valid_zones_names:
            zones_start.append(self.find_hub(zone))

        max_drones = 0
        for zn in zones_start:
            connection = self.find_connection(self.start_hub.name, zn.name)
            if not connection:
                raise ValueError(
                    "Algorithm failed trying to find a valid path")
            if (connection.max_link_capacity < zn.max_drones or
                    zn == self.end_hub):
                max_drones += connection.max_link_capacity
            else:
                max_drones += zn.max_drones

        return max_drones

    def find_path(self) -> None:

        total_bottleneck = self.find_total_bottleneck()

        self.create_drones(self.nb_drones)

        for i in range(self.nb_drones):

            list_tries: list[list[int]] = []

            if i > 2:
                self.clean_dist_hubs()
                if self.find_shortest_path(i // total_bottleneck):
                    first_try = self.dist_hubs[self.end_hub].distance
                    if first_try is not None:
                        first_try = first_try + i // total_bottleneck
                        list_tries.append(
                            [first_try, i - i // total_bottleneck])

            if i - 2 >= 0:
                self.clean_dist_hubs()
                if self.find_shortest_path(i - 2):
                    second_try = self.dist_hubs[self.end_hub].distance
                    if second_try is not None:
                        second_try = second_try + i - 2
                        list_tries.append([second_try, 2])

            if i - 1 >= 0:
                self.clean_dist_hubs()
                if self.find_shortest_path(i - 1):
                    third_try = self.dist_hubs[self.end_hub].distance
                    if third_try is not None:
                        third_try = third_try + i - 1
                        list_tries.append([third_try, 1])

            self.clean_dist_hubs()
            if self.find_shortest_path(i):
                fourth_try = self.dist_hubs[self.end_hub].distance
                if fourth_try is not None:
                    fourth_try = fourth_try + i
                    list_tries.append([fourth_try, 0])

            if len(list_tries) == 0:
                raise Exception("Algorithm couldn't find a valid path")

            best_try = list_tries[0]

            for j in range(len(list_tries)):
                if list_tries[j][0] < best_try[0]:
                    best_try = list_tries[j]

            self.clean_dist_hubs()
            self.find_shortest_path(i - best_try[1])

            path = self.create_path()

            self.list_drones[i].path = path

            self.create_drone_turns(i - best_try[1], self.list_drones[i])

            self.update_hubs_connec_occupancy(
                path, i - best_try[1], self.list_drones[i])
