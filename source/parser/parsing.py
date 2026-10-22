# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   parsing.py                                          :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/09 13:54:46 by vivozzo-           #+#    #+#             #
#   Updated: 2026/09/24 14:11:24 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #


from building import Hub, Connection


class Parser:

    def __init__(self) -> None:
        self.config: list[list[str]] = []
        self.hub_names: list[str] = []
        self.errors = ""
        self.line_index: list[int] = []
        self.hub_names_zones: list[list[str]] = []
        self.nb_drones_data: str = ""
        self.hub_data: dict[str, list[str]] = {}
        self.connection_data: dict[str, list[list[str]]] = {}
        self.graph: dict[str, list[str]] = {}

    def check_metadata_connection(self, metadata: str, line: int,
                                  first_name: str) -> str:
        metadata_connection = []

        if metadata[0] != "[" or metadata[len(metadata) - 1] != "]":
            return (f"Invalid metadata syntax at line {line}, "
                    "must be: <name1>-<name2> [max_link_capacity=<number>], "
                    "metadata is optional\n")

        metadata = metadata[1:-1]
        metadata = metadata.strip()

        if metadata.count("=") != 1:
            return (f"Invalid metadata syntax at line {line}, "
                    "must be: <name1>-<name2> [max_link_capacity=<number>], "
                    "metadata is optional\n")

        metadata_connection = metadata.split("=")
        if (metadata_connection[0] == "" or metadata_connection[1] == "" or
                metadata_connection[0] != "max_link_capacity"):
            return (f"Invalid metadata syntax at line {line}, "
                    "must be: <name1>-<name2> [max_link_capacity=<number>], "
                    "metadata is optional\n")

        if (not metadata_connection[1].isdigit() or
                int(metadata_connection[1]) <= 0):
            return f"max_link_capacity at line {line} must be greater than 0\n"

        if self.errors == "":
            self.connection_data[first_name][-1][1] = metadata_connection[1]

        return ""

    # check connection only if the check hub and check_nb_drones was ok

    def check_connection(self) -> None:
        connections = []
        start_hub = ""
        end_hub = ""

        # Initialize graph with all known hubs.
        for hub in self.hub_names:
            self.graph[hub] = []
            self.connection_data[hub] = []

        i = 0
        for data in self.config:
            if data[0] == "start_hub":
                start_hub = data[1].split()[0]
            elif data[0] == "end_hub":
                end_hub = data[1].split()[0]
            if data[0] == "connection":
                connection_split = data[1].split(maxsplit=1)
                connection_names = connection_split[0]
                if connection_names.count("-") != 1:
                    self.errors += ("Invalid connection syntax at line "
                                    f"{self.line_index[i]}, "
                                    "must be: <name1>-<name2> [metadata], "
                                    "metadata is optional\n")
                    i += 1
                    continue
                first_name, second_name = connection_names.split("-")

                if first_name == "":
                    self.errors += ("First name at connection in line "
                                    f"{self.line_index[i]} is empty\n")
                elif first_name not in self.hub_names:
                    self.errors += ("First name at connection in line "
                                    f"{self.line_index[i]} does not exist\n")
                if second_name == "":
                    self.errors += ("Second name at connection in line "
                                    f"{self.line_index[i]} is empty\n")
                elif second_name not in self.hub_names:
                    self.errors += ("Second name at connection in line "
                                    f"{self.line_index[i]} does not exist\n")
                if (first_name == second_name):
                    self.errors += (f"Connection at line {self.line_index[i]} "
                                    "has the same hub name on both sides\n")
                elif (connection_names in connections or
                        f"{second_name}-{first_name}" in connections):
                    self.errors += (f"Connection at line {self.line_index[i]} "
                                    "already exists\n")
                elif (first_name in self.hub_names and
                      second_name in self.hub_names):
                    connections.append(connection_names)
                    self.connection_data[first_name].append([second_name, "1"])
                    # Bidirectional connection.
                    self.graph[first_name].append(second_name)
                    self.graph[second_name].append(first_name)

                if len(connection_split) == 2:
                    metadata_error = self.check_metadata_connection(
                        connection_split[1], self.line_index[i],
                        first_name)
                    if metadata_error != "":
                        self.errors += metadata_error

            i += 1

        if self.errors != "":
            return

        for name, zone in self.hub_names_zones:
            if zone == "blocked":
                del self.graph[name]

                for neighbours in self.graph.values():
                    if name in neighbours:
                        neighbours.remove(name)

        # Breadth-First Search (BFS)
        queue = [start_hub]
        visited = [start_hub]

        while queue:
            current_hub = queue.pop(0)
            if current_hub == end_hub:
                return
            for neighbour in self.graph[current_hub]:
                if neighbour not in visited:
                    visited.append(neighbour)
                    queue.append(neighbour)

        self.errors += (
            f"There is no connection between start_hub '{start_hub}' "
            f"and end_hub '{end_hub}'\n"
        )

    def check_nb_drones(self) -> None:

        for data in self.config:
            if data[0] == "nb_drones":
                if not data[1].strip().isdigit() or int(data[1].strip()) <= 0:
                    self.errors += ("nb_drones at first line "
                                    "must be a positive integer\n")
                    break
                self.nb_drones_data = data[1].strip()

    def check_metadata_hub(self, metadata: str, line: int, key: str,
                           flag_start_end_hub: bool, name: str) -> str:
        metadata_list = []
        metadata_allowed = ["zone", "color", "max_drones"]
        zone_allowed = ["normal", "blocked", "restricted", "priority"]
        errors = ""

        if metadata[0] != "[" or metadata[len(metadata) - 1] != "]":
            return (f"Invalid metadata syntax at line {line}, "
                    f"must be: {key}: <name> <x> <y> [data_type=data, ...]\n")

        # delete '[]' from metadata, first and last char
        metadata = metadata[1:-1]

        metadata_list = metadata.split()
        if not flag_start_end_hub:
            if len(metadata_list) == 0 or len(metadata_list) > 3:
                return (f"Invalid metadata syntax at line {line}, "
                        f"must be: {key}: <name> <x> <y> "
                        "[data_type= data, ...],"
                        "with maximum of three data types: 'zone', "
                        "'color' and 'max_drones'\n")
        else:
            if len(metadata_list) == 0:
                return (f"Invalid metadata syntax at line {line}, "
                        f"must be: {key}: <name> <x> <y> "
                        "[data_type= data, ...],"
                        "with maximum of two data types: 'zone' and 'color', "
                        "max_drones are ignored\n")

        count_zone = 0
        count_color = 0
        count_max_drones = 0
        metadata_divided = []

        for data in metadata_list:
            if data.count("=") != 1:
                return (f"Invalid metadata syntax at line {line}, "
                        f"must be: {key}: <name> <x> <y> "
                        "[data_type=data, ...]\n")
            else:
                metadata_divided = data.split("=")
            if metadata_divided[0] == "zone":
                count_zone += 1
                self.hub_names_zones.append([name, metadata_divided[1]])
            elif metadata_divided[0] == "color":
                count_color += 1
            elif (metadata_divided[0] == "max_drones"
                  and not flag_start_end_hub):
                count_max_drones += 1

        if count_zone > 1:
            errors += (f"Invalid metadata at line {line}, "
                       "must be only one 'zone'\n")
        if count_color > 1:
            errors += (f"Invalid metadata at line {line}, "
                       "must be only one 'color'\n")
        if count_max_drones > 1:
            errors += (f"Invalid metadata at line {line}, "
                       "must be only one 'max_drones'\n")

        if len(errors) != 0:
            return errors

        if count_zone == 1:
            for data in metadata_list:
                metadata_divided = data.split("=")
                if metadata_divided[0] == "zone":
                    self.hub_data[name].append(metadata_divided[1])
        else:
            self.hub_data[name].append("normal")

        if count_color == 1:
            for data in metadata_list:
                metadata_divided = data.split("=")
                if metadata_divided[0] == "color":
                    self.hub_data[name].append(metadata_divided[1])
        else:
            self.hub_data[name].append("none")

        if count_max_drones == 1:
            for data in metadata_list:
                metadata_divided = data.split("=")
                if metadata_divided[0] == "max_drones":
                    self.hub_data[name].append(metadata_divided[1])
        else:
            self.hub_data[name].append("1")

        for data in metadata_list:
            metadata_divided = data.split("=")

            if metadata_divided[0] == "" or metadata_divided[1] == "":
                errors += (f"Invalid metadata syntax at line {line}, must be: "
                           f"{key}: <name> <x> <y> [data_type=data, ...]\n")
            elif metadata_divided[0] not in metadata_allowed:
                errors += (f"{metadata_divided[0]} is not allowed in the "
                           "metadata, allowed: 'zone', "
                           "'color' and 'max_drones'\n")
            elif (metadata_divided[0] == "zone" and
                  metadata_divided[1] not in zone_allowed):
                errors += (f"Zone {metadata_divided[0]} at line {line} "
                           "is not allowed, must be: 'normal', 'blocked', "
                           "'restricted' or 'priority'\n")
            elif (metadata_divided[0] == "max_drones" and
                  (not metadata_divided[1].isdigit() or
                   int(metadata_divided[1]) == 0) and
                    not flag_start_end_hub):
                errors += (f"max_drones value at line {line} "
                           "must be greater than 0\n")

        return errors

    def check_hub(self) -> None:
        value_list = []
        hub_list = ["start_hub", "end_hub", "hub"]
        coords = []

        i = 0
        for data in self.config:
            if data[0] in hub_list:
                value_list = data[1].split(maxsplit=3)

                if len(value_list) < 3:
                    self.errors += ("Invalid syntax at line "
                                    f"{self.line_index[i]}, must be: "
                                    f"{data[0]}: <name> <x> <y> [metadata] , "
                                    "'metadata' is optional\n")
                    i += 1
                    continue

                name = value_list[0]

                self.hub_data[name] = []

                if name in self.hub_names:
                    self.errors += (f"Name at line {self.line_index[i]} "
                                    "already exists\n")
                elif "-" in name:
                    self.errors += ("Invalid name at line "
                                    f"{self.line_index[i]}, "
                                    "name cannot have '-'\n")
                else:
                    self.hub_names.append(name)

                self.hub_data[name].append(data[0])

                flag_first_coord = True
                flag_second_coord = True

                try:
                    int(value_list[1])
                except ValueError:
                    flag_first_coord = False

                try:
                    int(value_list[2])
                except ValueError:
                    flag_second_coord = False

                if flag_first_coord and flag_second_coord:
                    if f"{value_list[1]}.{value_list[2]}" in coords:
                        self.errors += ("Coordinates at line "
                                        f"{self.line_index[i]} "
                                        "already exists\n")
                    else:
                        coords.append(f"{value_list[1]}.{value_list[2]}")

                if not flag_first_coord:
                    self.errors += (f"First coordinate of {data[0]} at "
                                    f"line {self.line_index[i]} "
                                    "must be an integer\n")

                if not flag_second_coord:
                    self.errors += (f"Second coordinate of {data[0]} at "
                                    f"line {self.line_index[i]} "
                                    "must be an integer\n")

                self.hub_data[name].append(value_list[1])
                self.hub_data[name].append(value_list[2])

                if len(value_list) == 4:
                    if data[0] == "start_hub" or data[0] == "end_hub":
                        error_check_metadata = self.check_metadata_hub(
                            value_list[3], self.line_index[i],
                            data[0], True, name)
                    else:
                        error_check_metadata = self.check_metadata_hub(
                            value_list[3], self.line_index[i],
                            data[0], False, name)
                    if error_check_metadata != "":
                        self.errors += error_check_metadata
                else:
                    self.hub_names_zones.append([name, "normal"])
                    self.hub_data[name].append("normal")
                    self.hub_data[name].append("none")
                    self.hub_data[name].append("1")

            i += 1

    # check if there is an invalid input,
    # first check if there is a line without just 1 ":"
    # after that, check if the first line is nb_drones,
    # if there is only one start_hub and end_hub
    # check if there is atleast one connection

    def check_invalid_format_input(self, config_list: list[str]) -> None:
        config_list_split = []
        allowed_keys = ["nb_drones", "start_hub",
                        "end_hub", "hub", "connection"]

        # check invalid inputs, with the exactly line
        for i in range(len(config_list)):
            if config_list[i].count(":") != 1:
                self.errors += f"Invalid syntax at line {self.line_index[i]}\n"

        if len(self.errors) != 0:
            return

        i = 0
        for data in config_list:
            config_list_split = data.split(":")
            if config_list_split[0] != "" and config_list_split[1] != "":
                self.config.append(
                    [config_list_split[0].strip(),
                     config_list_split[1].strip()])
            else:
                self.errors += ("Data and/or data type at line "
                                f"{self.line_index[i]} is empty\n")
            i += 1

        if len(self.errors) != 0:
            return

        # check nb_drones, start_hub, end_hub and connections
        i = 0
        start_hub_count = 0
        end_hub_count = 0
        connection_count = 0
        for entry in self.config:
            if i == 0 and entry[0] != "nb_drones":
                self.errors += ("First line of the configuration "
                                "file must be 'nb_drones'\n")
            elif i != 0 and entry[0] == "nb_drones":
                self.errors += ("'nb_drones' found in line "
                                f"{self.line_index[i]}, "
                                "must be only in the first line\n")
            elif entry[0] not in allowed_keys:
                self.errors += ("Invalid data type in the configuration "
                                f"file at line {self.line_index[i]}, "
                                "must be: 'nb_drones', 'start_hub', "
                                "'end_hub', 'hub' or 'connection', "
                                "nb_drones must be in the first line\n")
            elif entry[0] == "start_hub":
                start_hub_count += 1
                if start_hub_count > 1:
                    self.errors += ("Should have only one start_hub in the "
                                    "configuration file, there is another "
                                    "start_hub in line "
                                    f"{self.line_index[i]}\n")
            elif entry[0] == "end_hub":
                end_hub_count += 1
                if end_hub_count > 1:
                    self.errors += ("Should have only one end_hub in the "
                                    "configuration file, there is another "
                                    f"end_hub in line {self.line_index[i]}\n")

            if entry[0] == "connection":
                connection_count += 1

            i += 1

        if start_hub_count == 0:
            self.errors += "There must be exactly one start_hub\n"

        if end_hub_count == 0:
            self.errors += "There must be exactly one end_hub\n"

        if connection_count == 0:
            self.errors += ("There is no connection in the "
                            "configuration file\n")

    # just read the config file and save all the lines
    # (return a tuple, the first element
    # is the config list and the second is a error message -
    # if there isnt an error, it will
    # be empty

    def read_config(self, map_path: str) -> tuple[list[str], str]:
        config_list = []

        i = 0
        try:
            with open(map_path, "r") as file:
                for line in file:
                    line = line.strip()

                    i += 1
                    if not line or line[0] == "#":
                        continue

                    config_list.append(line)
                    self.line_index.append(i)

                if len(config_list) == 0:
                    return ([], f"Empty file: {map_path}")
        except Exception as e:
            return ([], f"Error opening the map file: {e}")

        return (config_list, "")

    def parsing(self, argv: list[str]) -> tuple[int, list[Hub],
                                                list[Connection], Hub, Hub]:
        allowed_flags = ["--visual_output", "--benchmark"]

        if len(argv) != 2:
            if ((len(argv) == 3 and argv[2] not in allowed_flags) or
                    len(argv) != 3):
                raise Exception("Usage: python3 fly_in.py <map.txt> "
                                "[optional flag], allowed flags: "
                                f"{allowed_flags[0]} and {allowed_flags[1]}")

        config_list = self.read_config(argv[1])
        if config_list[1] != "":
            raise Exception(config_list[1])

        self.check_invalid_format_input(config_list[0])
        if self.errors != "":
            raise Exception(self.errors)

        self.check_hub()
        self.check_nb_drones()
        if self.errors != "":
            raise Exception(self.errors)

        self.check_connection()

        if self.errors != "":
            raise Exception(self.errors)

        list_hub: list[Hub] = []
        list_connection: list[Connection] = []

        for key, value in self.hub_data.items():
            if value[0] == "start_hub":
                start_hub = Hub(key, int(value[1]), int(value[2]),
                                value[3], value[4], int(value[5]))
            elif value[0] == "end_hub":
                end_hub = Hub(key, int(value[1]), int(value[2]),
                              value[3], value[4], int(value[5]))
            else:
                hub = Hub(key, int(value[1]), int(value[2]),
                          value[3], value[4], int(value[5]))
                list_hub.append(hub)

        for con_key, con_value in self.connection_data.items():
            for i in range(len(con_value)):
                connection = Connection(con_key, con_value[i][0],
                                        int(con_value[i][1]))
                list_connection.append(connection)

        return (int(self.nb_drones_data), list_hub,
                list_connection, start_hub, end_hub)
