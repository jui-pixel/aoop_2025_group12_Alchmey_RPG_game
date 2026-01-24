import pygame
import os
from typing import Dict, Any

class ResourceManager:
    """
    Handles loading and caching of game assets (images, audio, etc.).
    """
    def __init__(self, asset_base_path="assets"):
        self.base_path = asset_base_path
        self._images: Dict[str, pygame.Surface] = {}
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._fonts: Dict[str, pygame.font.Font] = {}

    def get_image(self, path: str) -> pygame.Surface:
        if path not in self._images:
            full_path = os.path.join(self.base_path, "images", path)
            try:
                self._images[path] = pygame.image.load(full_path).convert_alpha()
            except FileNotFoundError:
                print(f"ResourceManager: Image not found at {full_path}")
                # Return a generic placeholder (magenta square)
                s = pygame.Surface((32, 32))
                s.fill((255, 0, 255))
                self._images[path] = s
        return self._images[path]

    def get_sound(self, path: str) -> pygame.mixer.Sound:
        if path not in self._sounds:
            full_path = os.path.join(self.base_path, "audio", path)
            try:
                self._sounds[path] = pygame.mixer.Sound(full_path)
            except FileNotFoundError:
                print(f"ResourceManager: Sound not found at {full_path}")
                return None
        return self._sounds[path]
    
    def get_font(self, path: str, size: int) -> pygame.font.Font:
        key = f"{path}_{size}"
        if key not in self._fonts:
             full_path = os.path.join(self.base_path, "fonts", path)
             try:
                 self._fonts[key] = pygame.font.Font(full_path, size)
             except FileNotFoundError:
                 print(f"ResourceManager: Font not found at {full_path}, using default.")
                 self._fonts[key] = pygame.font.SysFont("Arial", size)
        return self._fonts[key]
