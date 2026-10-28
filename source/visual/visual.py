# *************************************************************************** #
#                                                                             #
#                                                         :::      ::::::::   #
#   terminal.py                                         :+:      :+:    :+:   #
#                                                     +:+ +:+         +:+     #
#   By: vivozzo- <vivozzo-@student.42porto.com>     +#+  +:+       +#+        #
#                                                 +#+#+#+#+#+   +#+           #
#   Created: 2026/09/17 17:03:18 by vivozzo-           #+#    #+#             #
#   Updated: 2026/09/22 14:58:10 by vivozzo-          ###   ########.fr       #
#                                                                             #
# *************************************************************************** #

import pygame
from sys import exit
from building import Hub, Connection, Drone
from visual import TerminalOutput
import math


class Camera:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

        self.dragging = False
        self.last_mouse_pos: tuple[int, int] = (0, 0)

    def handle_event(self, event: pygame.event.Event) -> None:

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
        return (
            x - self.x,
            y - self.y
        )


class VisualOutput:
    def __init__(self, list_drones: list[Drone], list_hub: list[Hub],
                 list_connection: list[Connection], start_hub: Hub,
                 end_hub: Hub, file_name: str) -> None:
        self.list_drones = list_drones
        self.list_hub = list_hub
        self.list_connection = list_connection
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.file_name = file_name.split("/")[-1]
        self.adjust_zones_coord = (0, 0)
        self.coord_adjust_mult = 0

    def find_hub(self, hub_name: str) -> Hub:
        for hb in self.list_hub:
            if hb.name == hub_name:
                return hb
        if hub_name == self.start_hub.name:
            return self.start_hub
        if hub_name == self.end_hub.name:
            return self.end_hub

        raise ValueError(f"Hub '{hub_name}' not found")

    def create_drones_coord(self) -> list[list[tuple[int, int]]]:
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
                        camera: Camera, background: pygame.Surface) -> None:
        tile_width = background.get_width()
        tile_height = background.get_height()

        start_x = int(camera.x // tile_width) * tile_width
        start_y = int(camera.y // tile_height) * tile_height

        end_x = camera.x + screen.get_width()
        end_y = camera.y + screen.get_height()

        for world_x in range(
            start_x,
            int(end_x) + tile_width,
            tile_width
        ):
            for world_y in range(
                start_y,
                int(end_y) + tile_height,
                tile_height
            ):
                screen_x = world_x - camera.x
                screen_y = world_y - camera.y

                screen.blit(
                    background,
                    (int(screen_x), int(screen_y))
                )

    def draw_zones(self, screen: pygame.Surface, camera: Camera,
                   zone_normal_surface: pygame.Surface,
                   font_start_end_zone: pygame.font.Font) -> None:

        def draw_zones_objects(coords_x: int, coords_y: int, hub: Hub) -> None:
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
                zone_rect = pygame.Rect(coords_x, coords_y, 50, 50)
                if hub.name == self.start_hub.name:
                    text_start = font_start_end_zone.render(
                        "START", True, "black")
                    text_start_rect = text_start.get_rect(
                        midbottom=(zone_rect.centerx, zone_rect.bottom + 34))
                    screen.blit(text_start, text_start_rect)
                elif hub.name == self.end_hub.name:
                    text_end = font_start_end_zone.render(
                        "END", True, "black")
                    text_end_rect = text_end.get_rect(
                        midbottom=(zone_rect.centerx, zone_rect.bottom + 34))
                    screen.blit(text_end, text_end_rect)

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
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
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

        width_align = width - 370
        height_between_align = 50
        if index <= total_turns:
            text_turn = font_turn_mode.render(
                "TURN: " + str(index), False, "black")
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
            height_controls = 430
            height_between_controls = height_between_align
            width_controls = width_align
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

        total_turns = TerminalOutput.find_total_turns(self.list_drones)
        if index < total_turns:
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
        pygame.init()
        self.adjust_zones_coord = (75, 350)
        self.coord_adjust_mult = 125

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

        zone_normal_surface = pygame.Surface((50, 50))
        background_surface = pygame.image.load(
            "source/visual/files/sky-clouds-8-bit.png").convert()
        drone_img = pygame.image.load(
            "source/visual/files/drone.png").convert_alpha()
        drone_img = pygame.transform.smoothscale(drone_img, (72, 72))
        connec_coord = self.create_connec_coord()
        drones_coord = self.create_drones_coord()

        camera = Camera()

        time_between_turns_initial = 1500.0  # initial time between turns in ms
        max_speed = 4  # max speed power 2: 2 ** (max_speed - 1)
        actual_speed = 1
        time_between_turns = time_between_turns_initial
        time_now = pygame.time.get_ticks()
        time_next_turn = time_now + time_between_turns
        total_turns = TerminalOutput.find_total_turns(self.list_drones)
        index = total_turns + 1

        is_paused = True
        is_backwards = False
        is_step_mode = False
        # limit to show the controls and legend - limit is x = 1545, y = 980 
        limit_show_controls = (1500, 900)

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
                        if is_step_mode and index < total_turns:
                            index += 1
                        if index == total_turns + 1:
                            index = 0
                    if event.key == pygame.K_LSHIFT:
                        if not is_paused:
                            is_paused = True
                        if is_backwards:
                            is_backwards = False
                        index = total_turns + 1
                    if event.key == pygame.K_r:
                        if is_paused or not is_backwards:
                            is_paused = False
                        else:
                            is_paused = True
                        if not is_backwards:
                            is_backwards = True
                        if is_step_mode and index > 0 and index <= total_turns:
                            index -= 1
                            if index == 0:
                                index = total_turns + 1
                        if not is_step_mode and index == total_turns:
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

            self.draw_background(screen, camera, background_surface)

            self.draw_connections(screen, camera, connec_coord, font_max_link)

            self.draw_zones(
                screen, camera, zone_normal_surface, font_start_end_zone)

            self.draw_map_text(is_step_mode, actual_speed, hide_controls,
                               index, total_turns,
                               font_turn_mode, screen, width, height,
                               font_controls, font_map_file_title,
                               font_zone_legend)

            self.drones_turns(screen, camera, drones_coord,
                              index, drone_img, font_id_drone)

            if (not is_paused and not is_step_mode and
                time_now >= time_next_turn and
                    index >= 0 and index < total_turns):
                if not is_backwards:
                    index += 1
                else:
                    if index != 0:
                        index -= 1
                    else:
                        index = total_turns + 1
                time_next_turn = time_now + time_between_turns

            # draw all elements and update everything
            pygame.display.update()
            clock.tick(60)  # max fps
