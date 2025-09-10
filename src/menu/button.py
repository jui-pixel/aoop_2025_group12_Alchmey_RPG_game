import pygame

class Button:
    def __init__(self, x, y, width, height, text, image, action, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = image
        self.font = font or pygame.font.SysFont(None, 36)  # Default font if none provided
        self.action = action
        self.is_selected = False
        self.available = True

    def draw(self, screen):
        # Draw button background
        color = (255, 255, 0) if self.is_selected else (100, 100, 100)
        pygame.draw.rect(screen, color, self.rect)
        # Draw text
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True, self.action
        return False, None