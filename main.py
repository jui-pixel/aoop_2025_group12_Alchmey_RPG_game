# main.py
import asyncio
import pygame
import platform
from src.game import Game
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Roguelike Dungeon")
clock = pygame.time.Clock()


async def main():
    game = Game(screen, clock)
    while True:
        dt = clock.tick(FPS) / 1000.0
        if not game.update(dt):
            break
        game.draw()
    pygame.quit()


if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
