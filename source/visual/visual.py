# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   visual.py                                           :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/17 17:03:18 by vivozzo-           #+#    #+#             #
#   Updated: 2026/10/29 13:52:43 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

import pygame
from sys import exit
from building import Hub, Connection, Drone
from visual import TerminalOutput
from math import hypot


class Camera:
    """Camera of the map, moved by dragging with the mouse.

    Attributes:
        x: Horizontal offset of the camera.
        y: Vertical offset of the camera.
        dragging: True while the left mouse button is held down.
        last_mouse_pos: Last mouse position seen while dragging.
    """

    def __init__(self) -> None:
        """Create a camera at the origin and not dragging."""

        self.x = 0
        self.y = 0

        self.dragging = False
        self.last_mouse_pos: tuple[int, int] = (0, 0)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Move the camera according to a mouse event.

        Pressing the left button starts the drag, moving the mouse while
        dragging scrolls the map and releasing the button ends the drag.

        Args:
            event: Pygame event to process.
        """

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.dragging = True
                self.last_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:

                x, y = event.pos
                old_x, old_y = self.last_mouse_pos

                self.x -= x - old_x
                self.y -= y - old_y

                self.last_mouse_pos = event.pos

    def world_to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Convert map coordinates to screen coordinates.

        Args:
            x: Horizontal position in the map.
            y: Vertical position in the map.

        Returns:
            The position on the screen, taking the camera offset into account.
        """

        return (
            x - self.x,
            y - self.y
        )


class Tooltip:
    """Small info box drawn next to the mouse cursor.

    The box is placed at an offset from the cursor and is flipped to the
    other side when it would go off the screen.

    Attributes:
        PADDING: Space in pixels between the border and the text.
        OFFSET: Distance in pixels between the cursor and the box.
        BG_COLOR: Background color as RGBA (semi-transparent).
        BORDER_COLOR: Color of the border, as RGB.
        TEXT_COLOR: Color of the text, as RGB.
        font: Font used to render the lines of text.
    """

    PADDING: int = 8
    OFFSET: int = 16
    BG_COLOR: tuple[int, int, int, int] = (10, 20, 40, 220)
    BORDER_COLOR: tuple[int, int, int] = (255, 255, 255)
    TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)

    def __init__(self, font: pygame.font.Font) -> None:
        """Store the font (create it once, not every frame).

        Args:
            font: Font used to render the lines of text.
        """
        self.font = font

    def draw(self, screen: pygame.Surface, lines: list[str],
             mouse_pos: tuple[int, int]) -> None:
        """Draw the box with one text line per entry in `lines`.

        Nothing is drawn if ``lines`` is empty.

        Args:
            screen: Surface where the box is drawn.
            lines: Text lines to show, one per entry.
            mouse_pos: Current position of the mouse cursor.
        """
        if not lines:
            return
        texts = [self.font.render(t, True, self.TEXT_COLOR) for t in lines]
        width = max(t.get_width() for t in texts) + 2 * self.PADDING
        height = sum(t.get_height() for t in texts) + 2 * self.PADDING

        x = mouse_pos[0] + self.OFFSET
        y = mouse_pos[1] + self.OFFSET
        screen_w, screen_h = screen.get_size()
        if x + width > screen_w:            # no space on the right: flip
            x = mouse_pos[0] - self.OFFSET - width
        if y + height > screen_h:           # no space below: flip
            y = mouse_pos[1] - self.OFFSET - height
        x, y = max(0, x), max(0, y)

        box = pygame.Surface((width, height), pygame.SRCALPHA)
        box.fill(self.BG_COLOR)
        pygame.draw.rect(box, self.BORDER_COLOR, box.get_rect(), 1)
        offset_y = self.PADDING
        for text in texts:
            box.blit(text, (self.PADDING, offset_y))
            offset_y += text.get_height()
        screen.blit(box, (x, y))


class VisualOutput:
    """Graphical (pygame) representation of the simulation.

    Shows the zones, the connections and the drones turn by turn, with
    controls to play, pause, reverse and change the speed.

    Attributes:
        list_drones: Drones with their timelines already computed.
        total_drones: Number of drones.
        list_hub: Regular hubs (without the start and end hubs).
        list_connection: All the connections of the map.
        start_hub: Starting zone.
        end_hub: Target zone.
        total_turns: Total number of simulation turns.
        file_name: Name of the map file.
        adjust_zones_coord: Pixel offset applied to all the zones.
        coord_adjust_mult: Pixels per map coordinate unit.
        total_drones_hub: For each zone, the ids of the drones in it at
            each turn (list index). Filled by ``create_total_drones_hub``.
    """

    def __init__(self, list_drones: list[Drone], list_hub: list[Hub],
                 list_connection: list[Connection], start_hub: Hub,
                 end_hub: Hub, file_name: str) -> None:
        """Create the visual output.

        Args:
            list_drones: Drones with their timelines already computed.
            list_hub: Regular hubs (without the start and end hubs).
            list_connection: All the connections of the map.
            start_hub: Starting zone.
            end_hub: Target zone.
            file_name: Path of the map file; only its name is kept.
        """

        self.list_drones = list_drones
        self.total_drones = len(list_drones)
        self.list_hub = list_hub
        self.list_connection = list_connection
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.total_turns = TerminalOutput.find_total_turns(self.list_drones)
        self.file_name = file_name.split("/")[-1]
        self.adjust_zones_coord = (0, 0)
        self.coord_adjust_mult = 0
        self.total_drones_hub: dict[Hub, list[list[int]]] = {}

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

    def create_drones_coord(self) -> list[list[tuple[int, int]]]:
        """Convert the timeline of every drone into pixel positions.

        For a zone, the position is the scaled zone coordinate. For a drone
        in flight on a connection, it is the midpoint between the two zones.

        Returns:
            For each drone, the ``(x, y)`` position at each turn.
        """

        i = 0
        drones_coord: list[list[tuple[int, int]]] = []
        for drone in self.list_drones:
            drones_coord.append([])
            for hub_connec in drone.turns:
                if "-" not in hub_connec:
                    hub = self.find_hub(hub_connec)
                    coords = (hub.first_coord * self.coord_adjust_mult +
                              self.adjust_zones_coord[0],
                              hub.second_coord * self.coord_adjust_mult +
                              self.adjust_zones_coord[1])
                    drones_coord[i].append(coords)
                else:
                    first_connec = hub_connec.split("-")[0]
                    second_connec = hub_connec.split("-")[1]
                    first_hub = self.find_hub(first_connec)
                    second_hub = self.find_hub(second_connec)
                    first_hub_coords = (first_hub.first_coord *
                                        self.coord_adjust_mult +
                                        self.adjust_zones_coord[0],
                                        first_hub.second_coord *
                                        self.coord_adjust_mult +
                                        self.adjust_zones_coord[1])
                    second_hub_coords = (second_hub.first_coord *
                                         self.coord_adjust_mult +
                                         self.adjust_zones_coord[0],
                                         second_hub.second_coord *
                                         self.coord_adjust_mult +
                                         self.adjust_zones_coord[1])
                    x_drone = ((second_hub_coords[0] - first_hub_coords[0])
                               // 2 + first_hub_coords[0])
                    y_drone = ((second_hub_coords[1] - first_hub_coords[1])
                               // 2 + first_hub_coords[1])
                    drones_coord[i].append((x_drone, y_drone))
            i += 1

        return drones_coord

    def create_connec_coord(self) -> list[tuple[tuple[int, int],
                                                tuple[int, int], int]]:
        """Convert the connections into pixel coordinates.

        Returns:
            For each connection, a tuple ``(first_zone_position,
            second_zone_position, max_link_capacity)``.
        """

        connec_coord: list[tuple[tuple[int, int], tuple[int, int], int]] = []

        for connec in self.list_connection:
            first_hub = self.find_hub(connec.first_name)
            second_hub = self.find_hub(connec.second_name)
            connec_coord.append(((first_hub.first_coord *
                                  self.coord_adjust_mult +
                                  self.adjust_zones_coord[0],
                                  first_hub.second_coord *
                                  self.coord_adjust_mult +
                                  self.adjust_zones_coord[1]),
                                 (second_hub.first_coord *
                                  self.coord_adjust_mult +
                                  self.adjust_zones_coord[0],
                                  second_hub.second_coord *
                                  self.coord_adjust_mult +
                                  self.adjust_zones_coord[1]),
                                 connec.max_link_capacity))

        return connec_coord

    def draw_background(self, screen: pygame.Surface,
                        camera: Camera) -> None:
        """Fill the screen and draw a grid aligned with map coordinates.

        The grid has one line per coordinate unit (``coord_adjust_mult``
        pixels apart) and moves together with the camera, so it always
        stays aligned with the zones.

        Args:
            screen: Surface where the background is drawn.
            camera: Camera that gives the current offset.
        """
        screen.fill((200, 205, 212))
        step = self.coord_adjust_mult
        width, height = screen.get_size()
        # +25: the grid passes through the centre of each zone (50x50)
        start_x = (self.adjust_zones_coord[0] + 25 - camera.x) % step
        start_y = (self.adjust_zones_coord[1] + 25 - camera.y) % step
        for x in range(int(start_x), width, step):
            pygame.draw.line(screen, (180, 186, 194), (x, 0), (x, height))
        for y in range(int(start_y), height, step):
            pygame.draw.line(screen, (180, 186, 194), (0, y), (width, y))

    def hub_screen_rect(self, camera: Camera, hub: Hub) -> pygame.Rect:
        """Return the 50x50 on-screen square of a zone.

        Args:
            camera: Camera that gives the current offset.
            hub: Zone to locate.

        Returns:
            The rectangle the zone occupies on the screen, taking the
            camera offset into account.
        """
        x, y = camera.world_to_screen(
            hub.first_coord * self.coord_adjust_mult
            + self.adjust_zones_coord[0],
            hub.second_coord * self.coord_adjust_mult
            + self.adjust_zones_coord[1])
        return pygame.Rect(x, y, 50, 50)

    def hub_under_mouse(self, camera: Camera,
                        mouse_pos: tuple[int, int]) -> Hub | None:
        """Return the zone under the cursor, or None.

        Checks the start zone, the end zone and then the regular zones,
        and returns the first one whose on-screen square contains the
        cursor.

        Args:
            camera: Camera that gives the current offset.
            mouse_pos: Current position of the mouse cursor.

        Returns:
            The zone under the cursor, or ``None`` if there is none.
        """
        for hub in [self.start_hub, self.end_hub, *self.list_hub]:
            if self.hub_screen_rect(camera, hub).collidepoint(mouse_pos):
                return hub
        return None

    def create_total_drones_hub(self) -> None:
        """Precompute which drones are in each zone at every turn.

        Fills ``total_drones_hub`` with, for each zone, a list indexed by
        turn (from 0 to ``total_turns``) with the ids of the drones in it.
        For the end zone, the ids are those of the drones already delivered.
        It must be called once, before the viewer loop, so the tooltip and
        the START/END counters do not recalculate it every frame.
        """

        def drones_in_hub(hub: Hub, turn: int) -> list[int]:
            """Return the ids of the drones in a zone at the given turn.

            For the end zone, return the drones already delivered.

            Args:
                hub: Zone to check.
                turn: Turn to check.

            Returns:
                The drone ids, or an empty list if ``turn`` is after the
                last turn.
            """
            if turn > self.total_turns:
                return []
            if hub.name == self.end_hub.name:
                return [d.id for d in self.list_drones
                        if hub.name in d.turns[:turn + 1]]
            return [d.id for d in self.list_drones
                    if len(d.turns) > turn and d.turns[turn] == hub.name]

        for hub in [self.start_hub, self.end_hub, *self.list_hub]:
            self.total_drones_hub[hub] = []

        for i in range(self.total_turns + 1):
            for hb in [self.start_hub, self.end_hub, *self.list_hub]:
                self.total_drones_hub[hb].append(drones_in_hub(hb, i))

    def hub_tooltip_lines(self, hub: Hub, turn: int) -> list[str]:
        """Build the tooltip text: name, type, drones and occupancy.

        Uses the data precomputed by ``create_total_drones_hub``. A turn
        out of range (for example the reset state) shows no drones.

        Args:
            hub: Zone under the mouse.
            turn: Turn to represent.

        Returns:
            The lines of the tooltip. Start and end zones only show the
            number of drones; the other zones show the drone ids and the
            occupancy as ``current/max_drones``.
        """
        symbols: dict[str, str] = {"normal": "■", "restricted": "▲",
                                   "priority": "◆", "blocked": "●"}
        turns = self.total_drones_hub[hub]
        ids = turns[turn] if turn < len(turns) else []
        lines = [hub.name,
                 f"{symbols.get(hub.zone_type, '?')} {hub.zone_type}"]
        if hub.name in (self.start_hub.name, self.end_hub.name):
            lines.append(str(len(ids)))     # sem limite: só o número
        else:
            lines.append(" ".join(f"D{i}" for i in ids) or "-")
            lines.append(f"{len(ids)}/{hub.max_drones}")
        return lines

    def draw_zones(self, screen: pygame.Surface, camera: Camera,
                   zone_normal_surface: pygame.Surface,
                   font_start_end_zone: pygame.font.Font, turn: int) -> None:
        """Draw the zones and the START/END counters.

        Each zone is drawn according to its type (square for normal,
        triangle for restricted, diamond for priority and circle for
        blocked) using its color, or gray if the color is not valid. The
        start and end zones also show how many drones are in each at
        the given turn (for the end zone, the delivered drones), using
        the data of ``total_drones_hub``; out of range turns show 0.

        Args:
            screen: Surface where everything is drawn.
            camera: Camera that gives the current offset.
            zone_normal_surface: Reusable 50x50 surface for normal zones.
            font_start_end_zone: Font of the START and END labels.
            turn: Turn to represent.
        """

        def draw_zones_objects(coords_x: int, coords_y: int, hub: Hub) -> None:
            """Draw one zone and, if needed, its START or END label.

            Args:
                coords_x: Horizontal map position (recomputed from ``hub``).
                coords_y: Vertical map position (recomputed from ``hub``).
                hub: Zone to draw.
            """

            coords_x, coords_y = camera.world_to_screen(
                hub.first_coord *
                self.coord_adjust_mult +
                self.adjust_zones_coord[0],
                hub.second_coord *
                self.coord_adjust_mult +
                self.adjust_zones_coord[1])
            color = hub.color
            if color is None or color not in pygame.colordict.THECOLORS:
                color = "gray52"

            if hub.zone_type == "normal":
                zone_normal_surface.fill(color)
                screen.blit(
                    zone_normal_surface, (coords_x, coords_y))

            elif hub.zone_type == "priority":
                coords = [(coords_x + 25, coords_y),
                          (coords_x + 50, coords_y + 25),
                          (coords_x + 25, coords_y + 50),
                          (coords_x, coords_y + 25)]
                pygame.draw.polygon(screen, color, coords)
            elif hub.zone_type == "restricted":
                coords = [(coords_x, coords_y + 50),
                          (coords_x + 25, coords_y),
                          (coords_x + 50, coords_y + 50)]
                pygame.draw.polygon(screen, color, coords)
            elif hub.zone_type == "blocked":
                pygame.draw.circle(
                    screen, color, (coords_x + 25, coords_y + 25), 25)

            zone_rect = pygame.Rect(coords_x, coords_y, 50, 50)
            if hub.name == self.start_hub.name:
                text_start = font_start_end_zone.render(
                    "START", True, "black")
                text_start_rect = text_start.get_rect(
                    midbottom=(zone_rect.centerx, zone_rect.bottom + 40))
                screen.blit(text_start, text_start_rect)
                total_drones_hub = ((len(self.total_drones_hub[hub][turn]) if
                                     turn < self.total_turns + 1 else 0))
                text_total_start = font_start_end_zone.render(
                    f" {total_drones_hub}/{self.total_drones}",
                    True, "black")
                text_total_start_rect = text_total_start.get_rect(
                    midbottom=(zone_rect.centerx - 5, zone_rect.top - 23))
                screen.blit(text_total_start, text_total_start_rect)
            elif hub.name == self.end_hub.name:
                text_end = font_start_end_zone.render(
                    "END", True, "black")
                text_end_rect = text_end.get_rect(
                    midbottom=(zone_rect.centerx, zone_rect.bottom + 40))
                screen.blit(text_end, text_end_rect)
                total_drones_hub = ((len(self.total_drones_hub[hub][turn]) if
                                     turn < self.total_turns + 1 else 0))
                text_total_end = font_start_end_zone.render(
                    f" {total_drones_hub}/{self.total_drones}", True, "black")
                text_total_end_rect = text_total_end.get_rect(
                    midbottom=(zone_rect.centerx - 5, zone_rect.top - 23))
                screen.blit(text_total_end, text_total_end_rect)

        draw_zones_objects(self.start_hub.first_coord *
                           self.coord_adjust_mult +
                           self.adjust_zones_coord[0],
                           self.start_hub.second_coord *
                           self.coord_adjust_mult +
                           self.adjust_zones_coord[1], self.start_hub)

        draw_zones_objects(self.end_hub.first_coord *
                           self.coord_adjust_mult +
                           self.adjust_zones_coord[0],
                           self.end_hub.second_coord *
                           self.coord_adjust_mult +
                           self.adjust_zones_coord[1], self.end_hub)

        for hub in self.list_hub:
            draw_zones_objects(hub.first_coord *
                               self.coord_adjust_mult +
                               self.adjust_zones_coord[0],
                               hub.second_coord *
                               self.coord_adjust_mult +
                               self.adjust_zones_coord[1], hub)

    def draw_thick_line(self, screen: pygame.Surface, color: str,
                        p1: tuple[int, int],
                        p2: tuple[int, int], width: int) -> None:
        """Draw a line with a given thickness.

        Args:
            screen: Surface where the line is drawn.
            color: Color of the line.
            p1: Starting point.
            p2: Ending point.
            width: Thickness of the line in pixels.
        """

        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        length = hypot(dx, dy)
        if length == 0:
            return

        px = -dy / length * (width / 2)
        py = dx / length * (width / 2)
        points = [
            (x1 + px, y1 + py),
            (x2 + px, y2 + py),
            (x2 - px, y2 - py),
            (x1 - px, y1 - py),
        ]
        pygame.draw.polygon(screen, color, points)

    def draw_connections(self, screen: pygame.Surface,
                         camera: Camera,
                         connec_coord: list[tuple[tuple[int, int],
                                                  tuple[int, int], int]],
                         font_max_link: pygame.font.Font) -> None:
        """Draw the connections and their maximum capacity.

        Args:
            screen: Surface where everything is drawn.
            camera: Camera that gives the current offset.
            connec_coord: Connections as returned by ``create_connec_coord``.
            font_max_link: Font of the capacity numbers.
        """

        for connec in connec_coord:
            first_hub_coords = camera.world_to_screen(
                connec[0][0] + 25, connec[0][1] + 25)
            second_hub_coords = camera.world_to_screen(
                connec[1][0] + 25, connec[1][1] + 25)
            self.draw_thick_line(
                screen, "gray52", first_hub_coords, second_hub_coords, 7)

        for connec in connec_coord:
            first_hub_coords = camera.world_to_screen(
                connec[0][0] + 25, connec[0][1] + 25)
            second_hub_coords = camera.world_to_screen(
                connec[1][0] + 25, connec[1][1] + 25)
            max_link = str(connec[2])
            text_surface = font_max_link.render(max_link, False, "black")
            screen.blit(text_surface, ((first_hub_coords[0] -
                                        second_hub_coords[0]) // 2 +
                                       second_hub_coords[0] - 10,
                                       (first_hub_coords[1] -
                                        second_hub_coords[1]) // 2 +
                                       second_hub_coords[1] - 15))

    def draw_map_text(self, is_step_mode: bool, actual_speed: int,
                      hide_controls: bool,
                      index: int, total_turns: int,
                      font_turn_mode: pygame.font.Font,
                      screen: pygame.Surface, width: int, height: int,
                      font_controls: pygame.font.Font,
                      font_map_file_title: pygame.font.Font,
                      font_zone_legend: pygame.font.Font) -> None:
        """Draw the texts of the interface.

        Shows the turn, map name, mode (step or auto) and speed, and also
        the list of controls and the zone legend unless they are hidden.

        Args:
            is_step_mode: True in step mode, False in automatic mode.
            actual_speed: Current speed level (the speed is
                ``2 ** (actual_speed - 1)``).
            hide_controls: True to hide the controls and the legend.
            index: Current turn; a value above ``total_turns`` is shown as
                turn 0 (reset state).
            total_turns: Total number of turns.
            font_turn_mode: Font of the turn, mode and speed.
            screen: Surface where the texts are drawn.
            width: Width of the screen.
            height: Height of the screen.
            font_controls: Font of the list of controls.
            font_map_file_title: Font of the map name.
            font_zone_legend: Font of the zone legend.
        """

        width_align = width - 370
        height_between_align = 50
        if index <= total_turns:
            if self.total_turns < 100:
                text_turn = font_turn_mode.render(
                    "TURN: " + str(index) + f"/{self.total_turns}",
                    False, "black")
            else:
                text_turn = font_turn_mode.render(
                    "TURN: " + str(index), False, "black")
        else:
            if self.total_turns < 100:
                text_turn = font_turn_mode.render(
                    "TURN: 0" + f"/{self.total_turns}", False, "black")
            else:
                text_turn = font_turn_mode.render(
                    "TURN: 0", False, "black")
        screen.blit(text_turn, (width_align, 15))

        text_map_file_title = font_map_file_title.render(
            f"MAP FILE NAME: {self.file_name}", False, "black")
        text_map_file_rect = text_map_file_title.get_rect(topleft=((30,
                                                                   15)))
        screen.blit(text_map_file_title, text_map_file_rect)

        if is_step_mode:
            mode = "STEP"
        else:
            mode = "AUTO"
        text_mode = font_turn_mode.render(f"MODE: {mode}", False, "black")
        screen.blit(text_mode, (width_align, 85))

        if not is_step_mode:
            text_speed = font_turn_mode.render(
                f"SPEED: x {2 ** (actual_speed - 1)}", False, "black")
            screen.blit(text_speed, (width_align, 155))

        if not hide_controls:
            height_controls = 460
            height_between_controls = height_between_align
            width_controls = width_align + 55
            text_controls = font_controls.render("CONTROLS", False, "black")
            screen.blit(text_controls, (width_controls,
                        height_controls + height_between_controls/2))

            controls = ["NEXT TURN: SPACE", "REVERSE: R", "RESET: SHIFT",
                        "MODE: M", "↑SPEED: V", "↓SPEED: D",
                        "HIDE CONTROLS: H", "EXIT: ESC"]
            for i in range(len(controls)):
                text_controls = font_controls.render(controls[i],
                                                     False, "black")
                screen.blit(text_controls, (width_controls,
                            height_controls + height_between_controls * (i+2)))

            legend_padding = 25
            legend = ["ZONE LEGEND", "■ : NORMAL ZONE", "▲ : RESTRICTED ZONE",
                      "◆ : PRIORITY ZONE", "● : BLOCKED ZONE"]
            legend_rect = []

            text = font_zone_legend.render(
                legend[0], False, "black")
            text_rect = text.get_rect(
                bottomleft=(20, height - 30))
            legend_rect.append(text_rect)
            screen.blit(text, text_rect)

            for i in range(len(legend) - 1):
                text = font_zone_legend.render(legend[i + 1], False, "black")
                text_rect = text.get_rect(bottomleft=(20, height - 30))
                legend_rect.append(text_rect)
                text_rect.left = (legend_rect[i].right +
                                  legend_padding)
                screen.blit(text, text_rect)

    def drones_turns(self, screen: pygame.Surface, camera: Camera,
                     drones_coord: list[list[tuple[int, int]]], index: int,
                     drone_img: pygame.Surface,
                     font_id_drone: pygame.font.Font) -> None:
        """Draw the drones, with their ids, at a given turn.

        The id is not drawn while the drone is still in the start zone.
        Nothing is drawn once ``index`` reaches the total number of turns.

        Args:
            screen: Surface where the drones are drawn.
            camera: Camera that gives the current offset.
            drones_coord: Positions as returned by ``create_drones_coord``.
            index: Turn to represent.
            drone_img: Image used to draw each drone.
            font_id_drone: Font of the drone ids.
        """

        if index < self.total_turns:
            i = 1
            for drone in drones_coord:
                if index < len(drone):
                    drone_pos = camera.world_to_screen(drone[index][0] - 11,
                                                       drone[index][1] - 12)
                    screen.blit(drone_img, drone_pos)
                    drone_rect = pygame.Rect(
                        drone_pos[0], drone_pos[1], 72, 72)
                    if (self.start_hub.first_coord !=
                        (drone[index][0] - self.adjust_zones_coord[0]) /
                        self.coord_adjust_mult or
                            self.start_hub.second_coord !=
                            (drone[index][1] - self.adjust_zones_coord[1]) /
                            self.coord_adjust_mult):
                        text_drone_id = font_id_drone.render(
                            f"D{i}", True, "black")
                        text_drone_id_rect = text_drone_id.get_rect(
                            midbottom=(drone_rect.centerx,
                                       drone_rect.top + 12))

                        screen.blit(text_drone_id, text_drone_id_rect)
                i += 1

    def visual(self) -> None:
        """Open the window and run the simulation viewer.

        Loads the fonts and images, precomputes the drones of each zone and
        loops until the window is closed.
        Controls: SPACE plays/pauses (or goes to the next turn in step
        mode), R reverses, SHIFT resets, M switches between auto and step
        mode, V and D change the speed, H hides the controls and ESC exits.
        Dragging with the mouse moves the map and hovering a zone shows a
        tooltip with its drones. The program ends when the window is
        closed.
        """

        pygame.init()

        self.coord_adjust_mult = 125
        self.adjust_zones_coord = (
            75 - self.start_hub.first_coord * self.coord_adjust_mult,
            350 - self.start_hub.second_coord * self.coord_adjust_mult)

        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        width, height = screen.get_size()
        pygame.display.set_caption("FLY-IN SIMULATION")  # title
        clock = pygame.time.Clock()

        font_max_link = pygame.font.Font(None, 40)
        font_turn_mode = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 55)
        font_controls = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 30)
        font_map_file_title = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 35)
        font_zone_legend = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 30)
        font_id_drone = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 23)
        font_start_end_zone = pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 27)
        tooltip = Tooltip(pygame.font.Font(
            "source/visual/files/DejaVuSans.ttf", 24))

        zone_normal_surface = pygame.Surface((50, 50))
        drone_img = pygame.image.load(
            "source/visual/files/drone.png").convert_alpha()
        drone_img = pygame.transform.smoothscale(drone_img, (72, 72))
        connec_coord = self.create_connec_coord()
        drones_coord = self.create_drones_coord()
        self.create_total_drones_hub()

        camera = Camera()

        time_between_turns_initial = 1500.0  # initial time between turns in ms
        max_speed = 4  # max speed power 2: 2 ** (max_speed - 1)
        actual_speed = 1
        time_between_turns = time_between_turns_initial
        time_now = pygame.time.get_ticks()
        time_next_turn = time_now + time_between_turns
        index = self.total_turns + 1

        is_paused = True
        is_backwards = False
        is_step_mode = False
        # limit to show the controls and legend - limit is x = 1545, y = 950
        limit_show_controls = (1500, 870)

        if width < limit_show_controls[0] or height < limit_show_controls[1]:
            hide_controls = True
        else:
            hide_controls = False
        while True:

            time_now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
                    if event.key == pygame.K_SPACE:
                        if is_paused or is_backwards:
                            is_paused = False
                        else:
                            is_paused = True
                        if is_backwards:
                            is_backwards = False
                        if is_step_mode and index < self.total_turns:
                            index += 1
                        if index == self.total_turns + 1:
                            index = 0
                    if event.key == pygame.K_LSHIFT:
                        if not is_paused:
                            is_paused = True
                        if is_backwards:
                            is_backwards = False
                        index = self.total_turns + 1
                    if event.key == pygame.K_r:
                        if is_paused or not is_backwards:
                            is_paused = False
                        else:
                            is_paused = True
                        if not is_backwards:
                            is_backwards = True
                        if (is_step_mode and index > 0 and
                                index <= self.total_turns):
                            index -= 1
                            if index == 0:
                                index = self.total_turns + 1
                        if not is_step_mode and index == self.total_turns:
                            index -= 1
                            time_next_turn = time_now + time_between_turns
                    if event.key == pygame.K_m:
                        if not is_step_mode:
                            is_step_mode = True
                        else:
                            is_step_mode = False
                    if event.key == pygame.K_h:
                        if not hide_controls:
                            hide_controls = True
                        else:
                            hide_controls = False
                    if event.key == pygame.K_v:
                        if (time_between_turns > time_between_turns_initial /
                                (2 ** (max_speed - 1))):
                            time_between_turns /= 2
                            actual_speed += 1
                    if event.key == pygame.K_d:
                        if time_between_turns < time_between_turns_initial:
                            time_between_turns *= 2
                            actual_speed -= 1

                camera.handle_event(event)

            self.draw_background(screen, camera)

            self.draw_connections(screen, camera, connec_coord, font_max_link)

            self.draw_zones(
                screen, camera, zone_normal_surface, font_start_end_zone,
                index)

            self.drones_turns(screen, camera, drones_coord,
                              index, drone_img, font_id_drone)

            self.draw_map_text(is_step_mode, actual_speed, hide_controls,
                               index, self.total_turns,
                               font_turn_mode, screen, width, height,
                               font_controls, font_map_file_title,
                               font_zone_legend)

            mouse_pos = pygame.mouse.get_pos()
            mouse_hub = (None if camera.dragging
                         else self.hub_under_mouse(camera, mouse_pos))
            if mouse_hub is not None:
                pygame.draw.rect(
                    screen, (30, 30, 30),
                    self.hub_screen_rect(camera, mouse_hub).inflate(10, 10), 3)
                tooltip.draw(screen, self.hub_tooltip_lines(mouse_hub, index),
                             mouse_pos)

            if (not is_paused and not is_step_mode and
                time_now >= time_next_turn and
                    index >= 0 and index < self.total_turns):
                if not is_backwards:
                    index += 1
                else:
                    if index != 0:
                        index -= 1
                    else:
                        index = self.total_turns + 1
                time_next_turn = time_now + time_between_turns

            # draw all elements and update everything
            pygame.display.update()
            clock.tick(60)  # max fps
