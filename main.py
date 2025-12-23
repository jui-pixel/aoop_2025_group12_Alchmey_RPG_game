import pygame
import asyncio
from src.core.game import Game
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Roguelike Dungeon")
    clock = pygame.time.Clock()
    game = Game(screen, clock)
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())