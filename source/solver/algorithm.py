# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   algorithm.py                                        :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/21 10:58:09 by vivozzo-           #+#    #+#             #
#   Updated: 2026/10/30 17:54:05 by vivozzo-          ###   ########.fr       #
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

    def update_hubs_connec_occupancy(self, drone: Drone) -> None:
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

    # return if it has a path or not

    def find_shortest_path(self) -> bool:
        turn_cost_zone = {"normal": 1, "restricted": 2, "priority": 1}
        connections: list[str] = []
        visited_hubs: list[str] = []

        def find_total_wait(turn: int, hub_connection: Hub,
                            hub_visited: Hub) -> int:
            # need to check connection and hub vacancy,
            # if it is occupied, it will wait

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
        self.dist_hubs[self.start_hub] = DistInfo(0, None)
        for hub in list(self.list_hub):
            if hub.zone_type != "blocked" and hub.name in self.graph:
                self.dist_hubs[hub] = DistInfo(None, None)
        self.dist_hubs[self.end_hub] = DistInfo(None, None)

    def create_drone_turns(self, drone: Drone) -> None:

        def check_hub(prev: Hub, hub: Hub, turn: int) -> bool:
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
