from __future__ import annotations

from random import choice
from pathlib import Path

import pygame


SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
CENTER_POSITION = (
    (GRID_WIDTH // 2) * GRID_SIZE,
    (GRID_HEIGHT // 2) * GRID_SIZE,
)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

BOARD_BACKGROUND_COLOR = (0, 0, 0)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 69, 0)
SNAKE_COLOR = (0, 180, 80)

SPEED = 12
CELL_RECT_SIZE = (GRID_SIZE, GRID_SIZE)
HIGH_SCORE_FILE = Path(__file__).with_name("high_score.txt")
ALL_CELLS = {
    (x * GRID_SIZE, y * GRID_SIZE)
    for x in range(GRID_WIDTH)
    for y in range(GRID_HEIGHT)
}

TURN_BY_KEY = {
    (pygame.K_UP, LEFT): UP,
    (pygame.K_UP, RIGHT): UP,
    (pygame.K_DOWN, LEFT): DOWN,
    (pygame.K_DOWN, RIGHT): DOWN,
    (pygame.K_LEFT, UP): LEFT,
    (pygame.K_LEFT, DOWN): LEFT,
    (pygame.K_RIGHT, UP): RIGHT,
    (pygame.K_RIGHT, DOWN): RIGHT,
}

screen = None
clock = None


class GameObject:
    def __init__(
        self,
        position: tuple[int, int] = CENTER_POSITION,
        body_color: tuple[int, int, int] | None = None,
    ) -> None:
        self.position = position
        self.body_color = body_color

    def draw(self) -> None:
        pass

    def draw_cell(
        self,
        position: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        if screen is None:
            return

        rect = pygame.Rect(position, CELL_RECT_SIZE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Apple(GameObject):

    def __init__(
        self,
        occupied_positions: list[tuple[int, int]] | set[tuple[int, int]] | None = None,
    ) -> None:
        super().__init__(body_color=APPLE_COLOR)
        self.randomize_position(occupied_positions)

    def randomize_position(
        self,
        occupied_positions: list[tuple[int, int]] | set[tuple[int, int]] | None = None,
    ) -> None:
        occupied_cells = set(occupied_positions or ())
        free_cells = tuple(ALL_CELLS - occupied_cells)

        if not free_cells:
            raise ValueError("There are no free cells for a new apple.")

        self.position = choice(free_cells)

    def draw(self) -> None:
        self.draw_cell(self.position, self.body_color)


class Snake(GameObject):

    def __init__(self) -> None:
        super().__init__(body_color=SNAKE_COLOR)
        self.reset()

    def reset(self, position: tuple[int, int] = CENTER_POSITION) -> None:
        self.length = 1
        self.positions = [position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None
        self.position = position

    def update_direction(self) -> None:
        if self.next_direction is not None:
            self.direction = self.next_direction
            self.next_direction = None

    def get_head_position(self) -> tuple[int, int]:
        return self.positions[0]

    def get_next_head_position(self) -> tuple[int, int]:
        head_x, head_y = self.get_head_position()
        direction_x, direction_y = self.direction

        return (
            (head_x + direction_x * GRID_SIZE) % SCREEN_WIDTH,
            (head_y + direction_y * GRID_SIZE) % SCREEN_HEIGHT,
        )

    def grow(self) -> None:
        self.length += 1

    def move(self) -> bool:
        new_head = self.get_next_head_position()

        if self._has_self_collision(new_head):
            self.reset(new_head)
            return True

        self.positions.insert(0, new_head)
        self.position = new_head

        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

        return False

    def draw(self) -> None:
        for position in self.positions:
            self.draw_cell(position, self.body_color)

    def _has_self_collision(self, new_head: tuple[int, int]) -> bool:
        if len(self.positions) < 4:
            return False

        occupied_cells_after_tail_shift = self.positions[:-1]
        return new_head in occupied_cells_after_tail_shift


def handle_keys(game_object: Snake) -> bool:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False

            current_direction = game_object.next_direction or game_object.direction
            game_object.next_direction = TURN_BY_KEY.get(
                (event.key, current_direction),
                current_direction,
            )

    return True


def load_high_score() -> int:
    try:
        return int(HIGH_SCORE_FILE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(score: int) -> None:
    HIGH_SCORE_FILE.write_text(str(score), encoding="utf-8")


def update_caption(score: int, high_score: int) -> None:
    pygame.display.set_caption(f"Snake | length: {score} | record: {high_score}")


def main() -> None:
    global screen, clock

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    snake = Snake()
    apple = Apple(snake.positions)
    high_score = load_high_score()
    update_caption(snake.length, high_score)

    running = True
    while running:
        clock.tick(SPEED)
        running = handle_keys(snake)
        snake.update_direction()

        if snake.get_next_head_position() == apple.position:
            snake.grow()

        is_self_bite = snake.move()

        if snake.get_head_position() == apple.position and not is_self_bite:
            try:
                apple.randomize_position(snake.positions)
            except ValueError:
                snake.reset()
                apple.randomize_position(snake.positions)

        if snake.length > high_score:
            high_score = snake.length
            save_high_score(high_score)

        update_caption(snake.length, high_score)
        screen.fill(BOARD_BACKGROUND_COLOR)
        apple.draw()
        snake.draw()
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
