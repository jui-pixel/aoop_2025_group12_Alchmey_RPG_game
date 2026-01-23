import pygame
from typing import Tuple
from ..utils.helpers import get_project_path

class DamageText(pygame.sprite.Sprite):
    """A sprite to display floating damage numbers."""
    def __init__(self, pos: Tuple[float, float], damage: str, font_size: int = 32):
        super().__init__()
        self.pos = list(pos)
        self.damage = damage
        self.font_size = font_size
        self.color = (255, 0, 0)  # Red for damage

        # Load Silver.ttf
        font_path = get_project_path("assets", "fonts", "Silver.ttf")
        try:
            self.font = pygame.font.Font(font_path, self.font_size)
            print(f"成功載入字體: {font_path}")
        except Exception as e:
            print(f"無法載入 Silver.ttf: {e}，使用預設字體")
            self.font = pygame.font.SysFont(None, self.font_size)
        
        self.image = self.font.render(str(damage), True, self.color)
        self.rect = self.image.get_rect(center=self.pos)
        self.lifetime = 1.0  # Display for 1 second
        self.speed = -50.0  # Move upward at 50 pixels per second
        self.alpha = 255  # Start fully opaque

    def update(self, dt: float, current_time: float) -> bool:
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
    
    def draw(self, screen: pygame.Surface, camera_offset: Tuple[float, float]) -> None:
        """Draw the damage text on the screen with camera offset."""
        screen_pos = (self.rect.x - camera_offset[0], self.rect.y - camera_offset[1])
        screen.blit(self.image, screen_pos)