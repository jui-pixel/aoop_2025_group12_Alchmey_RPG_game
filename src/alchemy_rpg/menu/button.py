# src/menu/button.py
import pygame
from typing import Tuple

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, image: pygame.Surface, action: str, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.image = image
        self.image.set_alpha(200)
        self.image.fill((50, 50, 50))
        self.font = font or pygame.font.SysFont(None, 36)
        self.is_selected = False
        self.is_hovered = False
        self.available = True

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        if self.is_selected:
            pygame.draw.rect(screen, (0, 255, 0), self.rect, 2)
        elif self.is_hovered:
            pygame.draw.rect(screen, (255, 255, 0), self.rect, 2)

    def handle_event(self, event: pygame.event.Event) -> Tuple[bool, str]:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.available:
                return True, self.action
        return False, ""