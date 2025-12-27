import pytest
import os
import pygame

# 這段程式碼會在任何測試開始前自動執行
# 強制設定為無頭模式 (Headless)，避免 CI 報錯
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

@pytest.fixture(scope="session", autouse=True)
def init_pygame():
    """整個測試過程只初始化一次 Pygame"""
    pygame.init()
    yield
    pygame.quit()