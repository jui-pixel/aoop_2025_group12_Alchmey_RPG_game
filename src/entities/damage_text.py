import pygame
from typing import Tuple

class DamageText(pygame.sprite.Sprite):
    """A sprite to display floating damage numbers."""
    def __init__(self, pos: Tuple[float, float], damage: int):
        super().__init__()
        self.pos = list(pos)
        self.damage = damage
        self.font = pygame.font.SysFont(None, 24)
        self.color = (255, 0, 0)  # Red for damage
        self.image = self.font.render(str(damage), True, self.color)
        self.rect = self.image.get_rect(center=self.pos)
        self.lifetime = 1.0  # Display for 1 second
        self.speed = -50.0  # Move upward at 50 pixels per second
        self.alpha = 255  # Start fully opaque

    def update(self, dt: float) -> bool:
        """Update position and transparency, remove when lifetime expires."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return False
        # Move upward
        self.pos[1] += self.speed * dt
        self.rect.center = self.pos
        # Fade out
        self.alpha = max(0, self.alpha - 255 * dt / self.lifetime)
        self.image.set_alpha(int(self.alpha))
        return True