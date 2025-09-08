import pygame

class AudioManager:
    def __init__(self, game: 'Game'):
        self.game = game
        pygame.mixer.init()
        self.background_music = None
        self.sound_effects = {}
        self.load_sound_effect("skill_activate", "src/asserts/sounds/skill.wav")  # Default sound effect

    def load_background_music(self, file_path: str) -> None:
        """Load background music."""
        try:
            self.background_music = pygame.mixer.Sound(file_path)
        except Exception as e:
            print(f"Error loading background music: {e}")

    def play_background_music(self) -> None:
        """Play background music."""
        if self.background_music:
            self.background_music.play(-1)

    def stop_background_music(self) -> None:
        """Stop background music."""
        if self.background_music:
            self.background_music.stop()

    def load_sound_effect(self, name: str, file_path: str) -> None:
        """Load a sound effect."""
        try:
            self.sound_effects[name] = pygame.mixer.Sound(file_path)
        except Exception as e:
            print(f"Error loading sound effect {name}: {e}")

    def play_sound_effect(self, name: str) -> None:
        """Play a sound effect."""
        if name in self.sound_effects:
            self.sound_effects[name].play()