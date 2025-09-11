import pygame

class AudioManager:
    def __init__(self, game: 'Game'):
        """初始化音效管理器，負責管理背景音樂和音效。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game  # 保存遊戲實例引用
        pygame.mixer.init()  # 初始化 Pygame 音效模組
        self.background_music = None  # 用於儲存背景音樂的變數，初始為空
        self.sound_effects = {}  # 用於儲存音效的字典，鍵為音效名稱，值為音效對象
        self.load_sound_effect("skill_activate", "src/asserts/sounds/skill.wav")  # 預設載入技能啟動音效

    def load_background_music(self, file_path: str) -> None:
        """載入背景音樂文件。

        Args:
            file_path: 背景音樂文件的路徑。

        Raises:
            Exception: 如果載入音樂失敗，會捕獲並打印錯誤信息。
        """
        try:
            self.background_music = pygame.mixer.Sound(file_path)  # 載入背景音樂
        except Exception as e:
            print(f"錯誤：無法載入背景音樂 {file_path}，原因：{e}")

    def play_background_music(self) -> None:
        """播放背景音樂，循環播放。

        如果背景音樂已載入，則以無限循環方式播放。
        """
        if self.background_music:
            self.background_music.play(-1)  # -1 表示無限循環播放

    def stop_background_music(self) -> None:
        """停止播放背景音樂。

        如果背景音樂正在播放，則停止播放。
        """
        if self.background_music:
            self.background_music.stop()

    def load_sound_effect(self, name: str, file_path: str) -> None:
        """載入指定音效並儲存到音效字典中。

        Args:
            name: 音效的名稱，用於索引。
            file_path: 音效文件的路徑。

        Raises:
            Exception: 如果載入音效失敗，會捕獲並打印錯誤信息。
        """
        try:
            self.sound_effects[name] = pygame.mixer.Sound(file_path)  # 載入音效並存入字典
        except Exception as e:
            print(f"錯誤：無法載入音效 {name}，路徑：{file_path}，原因：{e}")

    def play_sound_effect(self, name: str) -> None:
        """播放指定名稱的音效。

        Args:
            name: 要播放的音效名稱。

        如果音效存在於字典中，則播放該音效。
        """
        if name in self.sound_effects:
            self.sound_effects[name].play()