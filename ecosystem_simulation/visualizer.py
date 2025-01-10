import os

import pygame
import pygame_gui
import time
from typing import Tuple

from PIL import Image

from ecosystem_simulation.simulator import *
from ecosystem_simulation.simulator.options import *
from ecosystem_simulation.simulation_player import *

BACKGROUND_COLOR = (200, 200, 200)
GRID_COLOR = (160, 160, 160)
PREDATOR_COLOR = (255, 0, 0)
PREY_COLOR = (0, 200, 50)
FOOD_COLOR = (0, 0, 255)
TEXT_COLOR = (0, 0, 0)


@dataclass
class Camera:
    x: float = 0
    y: float = 0
    zoom: float = 1.0

    def screen_to_world(self, screen_pos: Tuple[int, int], screen_size: Tuple[int, int]) -> Tuple[float, float]:
        screen_x, screen_y = screen_pos
        screen_width, screen_height = screen_size
        world_x = (screen_x - screen_width / 2) / self.zoom + self.x
        world_y = (screen_y - screen_height / 2) / self.zoom + self.y
        return world_x, world_y

    def world_to_screen(self, world_pos: Tuple[float, float], screen_size: Tuple[int, int]) -> Tuple[int, int]:
        world_x, world_y = world_pos
        screen_width, screen_height = screen_size
        screen_x = int((world_x - self.x) * self.zoom + screen_width / 2)
        screen_y = int((world_y - self.y) * self.zoom + screen_height / 2)
        return screen_x, screen_y


class EcosystemVisualizer:
    CELL_SIZE = 10

    def __init__(self, player: SimulationPlayer):
        pygame.init()
        self.player = player
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Ecosystem Simulation")

        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height))

        self.pause_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (100, 30)),
            text="Pause",
            manager=self.ui_manager
        )

        if (player.mode == PlayerMode.FILE):
            self.progress_slider = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect((20, self.screen_height - 40), (self.screen_width - 40, 30)),
                start_value=0.0,
                value_range=(0.0, 1.0),
                manager=self.ui_manager
            )

        self.speed_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((120, 10), (200, 30)),
            start_value=1.0,
            value_range=(0.1, 5.0),
            manager=self.ui_manager
        )


        self.speed_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((330, 10), (100, 30)),
            text="Speed: 1.0x",
            manager=self.ui_manager
        )

        self.paused = False
        self.simulation_speed = 1.0
        self.last_tick_time = time.time()
        self.tick_interval = 1.0 # seconds per tick

        self.camera = Camera()
        self.dragging = False
        self.last_mouse_pos = None

        self.font = pygame.font.Font(None, 36)

        self.current_tick = self.player.next_tick()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == pygame.BUTTON_WHEELUP:
                    self.camera.zoom *= 1.1
                elif event.button == pygame.BUTTON_WHEELDOWN:
                    self.camera.zoom /= 1.1

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False

            if event.type == pygame.MOUSEMOTION and self.dragging and not self.ui_manager.focused_set:
                current_pos = event.pos
                dx = (current_pos[0] - self.last_mouse_pos[0]) / self.camera.zoom
                dy = (current_pos[1] - self.last_mouse_pos[1]) / self.camera.zoom
                self.camera.x -= dx
                self.camera.y -= dy
                self.last_mouse_pos = current_pos

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.pause_button:
                    self.paused = not self.paused
                    self.pause_button.set_text("Resume" if self.paused else "Pause")

            if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.speed_slider:
                    self.simulation_speed = event.value
                    self.speed_label.set_text(f"Speed: {self.simulation_speed:.1f}x")
                elif event.ui_element == self.progress_slider:
                    self.player.tick = int(event.value * self.player.tick_count())

            self.ui_manager.process_events(event)

        return True

    def draw_entity(self, pos, color):
        cell_size = self.CELL_SIZE
        screen_pos = self.camera.world_to_screen((pos[0] * cell_size, pos[1] * cell_size), (self.screen_width, self.screen_height))
        pygame.draw.rect(self.screen, color, pygame.Rect(screen_pos[0], screen_pos[1], cell_size * self.camera.zoom, cell_size * self.camera.zoom))

    def draw_grid(self):
        world_width = self.player._options.world_width
        world_height = self.player._options.world_height
        cell_size = self.CELL_SIZE

        # Draw vertical lines
        for x in range(world_width + 1):
            start_pos = self.camera.world_to_screen((x * cell_size, 0), (self.screen_width, self.screen_height))
            end_pos = self.camera.world_to_screen((x * cell_size, world_height * cell_size), (self.screen_width, self.screen_height))
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos)

        # Draw horizontal lines
        for y in range(world_height + 1):
            start_pos = self.camera.world_to_screen((0, y * cell_size), (self.screen_width, self.screen_height))
            end_pos = self.camera.world_to_screen((world_width * cell_size, y * cell_size), (self.screen_width, self.screen_height))
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()


        # Draw entities
        for food in self.current_tick.state.food():
            self.draw_entity((food.position.x, food.position.y), FOOD_COLOR)

        for prey in self.current_tick.state.prey():
            self.draw_entity((prey.position.x, prey.position.y), PREY_COLOR)

        for predator in self.current_tick.state.predators():
            self.draw_entity((predator.position.x, predator.position.y), PREDATOR_COLOR)


        tick_text = self.font.render(f"Tick: {self.current_tick.tick_number}", True, TEXT_COLOR)
        self.screen.blit(tick_text, (10, 50))

        # Draw entity counts
        counts_text = self.font.render(
            f"Predators: {len(list(self.current_tick.state.predators()))} "
            f"Prey: {len(list(self.current_tick.state.prey()))} "
            f"Food: {len(list(self.current_tick.state.food()))}",
            True, TEXT_COLOR
        )
        self.screen.blit(counts_text, (10, 90))

        self.ui_manager.draw_ui(self.screen)
        pygame.display.flip()

    def update(self):
        current_time = time.time()
        if not self.paused:
            time_since_last_tick = current_time - self.last_tick_time
            if time_since_last_tick >= self.tick_interval / self.simulation_speed:
                self.current_tick = self.player.next_tick()
                self.last_tick_time = current_time

        self.ui_manager.update(current_time - self.last_tick_time)

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()

class EcosystemRecorder:
    CELL_SIZE = 10
    def __init__(self, simulator: EcosystemSimulator, num_ticks: int = 100):
        # headless mode (pygame)
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()

        self.simulator = simulator
        self.num_ticks = num_ticks

        # Calculate screen size
        margin = 40  # For text
        self.screen_width = simulator._options.world_width * self.CELL_SIZE + margin * 2
        self.screen_height = simulator._options.world_height * self.CELL_SIZE + margin * 2

        self.screen = pygame.Surface((self.screen_width, self.screen_height))

        # Center camera
        self.camera = Camera()
        self.camera.x = simulator._options.world_width / 2
        self.camera.y = simulator._options.world_height / 2
        self.camera.zoom = self.CELL_SIZE

        self.font = pygame.font.Font(None, 36)
        self.current_tick = self.simulator.next_simulation_tick()

        self.frames_list = []

    def draw_cell(self, pos: Tuple[float, float], color: Tuple[int, int, int]):
        screen_pos = self.camera.world_to_screen(pos, (self.screen_width, self.screen_height))
        rect = pygame.Rect(
            screen_pos[0],
            screen_pos[1],
            self.CELL_SIZE,
            self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, color, rect)

    def draw_grid(self):
        world_width = self.simulator._options.world_width
        world_height = self.simulator._options.world_height

        for x in range(world_width + 1):
            start = self.camera.world_to_screen((x, 0), (self.screen_width, self.screen_height))
            end = self.camera.world_to_screen((x, world_height), (self.screen_width, self.screen_height))
            pygame.draw.line(self.screen, GRID_COLOR, start, end)

        for y in range(world_height + 1):
            start = self.camera.world_to_screen((0, y), (self.screen_width, self.screen_height))
            end = self.camera.world_to_screen((world_width, y), (self.screen_width, self.screen_height))
            pygame.draw.line(self.screen, GRID_COLOR, start, end)

    def draw_frame(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()

        # Draw entities
        for food in self.current_tick.state.food():
            self.draw_cell((food.position.x, food.position.y), FOOD_COLOR)

        for prey in self.current_tick.state.prey():
            self.draw_cell((prey.position.x, prey.position.y), PREY_COLOR)

        for predator in self.current_tick.state.predators():
            self.draw_cell((predator.position.x, predator.position.y), PREDATOR_COLOR)

        # Draw tick number
        tick_text = self.font.render(f"Tick: {self.current_tick.tick_number}", True, TEXT_COLOR)
        self.screen.blit(tick_text, (10, 10))

    def capture_frame(self):
        string_image = pygame.image.tobytes(self.screen, 'RGB')
        return Image.frombytes('RGB', (self.screen_width, self.screen_height), string_image)

    def record(self, output_path: str, fps: int = 10):
        print(f"Recording {self.num_ticks} ticks...")

        for i in range(self.num_ticks):
            if i % 10 == 0:
                print(f"Recording tick {i}/{self.num_ticks}")

            self.draw_frame()
            self.frames_list.append(self.capture_frame())
            self.current_tick = self.simulator.next_simulation_tick()

        print("Saving GIF...")
        self.frames_list[0].save(
            output_path,
            save_all=True,
            append_images=self.frames_list[1:],
            duration=1000 // fps,  # milliseconds per frame
            loop=0
        )
        print(f"Saved GIF to {output_path}")

        pygame.quit()
    pass

def main():
    simulator = EcosystemSimulator(
        options_=SimulationOptions(
            randomness_seed=43098592,
            world_width=64,
            world_height=64,
            max_vision_distance=14,
            child_gene_mutation_chance_when_mating=0.1,
            child_gene_mutation_magnitude_when_mating=0.05,
            initial_number_of_food_items=8,
            food_item_spawning_rate_per_tick=0.5,
            predator=PredatorSimulationOptions(
                initial_number=6,
                initial_satiation_on_spawn=0.7,
                initial_reproductive_urge_on_spawn=0,
                pregnancy_duration_in_ticks=20,
                max_children_per_birth=2,
                satiation_per_one_eaten_prey=1,
                satiation_loss_per_tick=0.025
            ),
            prey=PreySimulationOptions(
                initial_number=30,
                initial_satiation_on_spawn=0.75,
                pregnancy_duration_in_ticks=16,
                initial_reproductive_urge_on_spawn=0.05,
                satiation_per_food_item=1,
                max_children_per_birth=4,
                satiation_loss_per_tick=0.02
            )
        )
    )

    visualizer = EcosystemVisualizer(simulator)
    visualizer.run()

    # Uncomment to record
    #recorder = EcosystemRecorder(simulator)
    #recorder.record("ecosystem_simulation.gif")


if __name__ == '__main__':
    main()