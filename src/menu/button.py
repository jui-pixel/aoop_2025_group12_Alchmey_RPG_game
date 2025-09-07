import pygame

class Button:
    def __init__(self, x, y, width, height, text, image, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = image
        self.font = self.image.get_rect(center = ((x+width)/2,(y+height)/2))
        self.action = action
        self.is_selected = False
        self.available = True

    def draw(self, screen):
        # 繪製按鈕背景
        color = (255, 255, 0) if self.is_selected else (100, 100, 100)
        pygame.draw.rect(screen, color, self.rect)
        # 繪製文字
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True, self.action
        return False, None