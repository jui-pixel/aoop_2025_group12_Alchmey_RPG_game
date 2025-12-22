# src/menu/menu_config.py
"""
菜單配置模組 - 統一管理菜單的回傳動作、參數和配置
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


# ============================================================================
# 基本動作類 - 所有菜單通用的基礎動作
# ============================================================================

class BasicAction(str, Enum):
    """基本菜單動作 - 所有菜單通用"""
    # 通用控制動作
    EXIT_MENU = "EXIT_MENU"
    
    # 遊戲狀態動作
    ENTER_LOBBY = "enter_lobby"
    EXIT_GAME = "exit"
    PAUSE_GAME = "pause_game"
    RESUME_GAME = "resume_game"


# ============================================================================
# 菜單導航類 - 專門用於菜單之間的切換
# ============================================================================

class MenuNavigation(str, Enum):
    """菜單導航動作 - 用於菜單切換"""
    # 主要菜單
    MAIN_MENU = "main_menu"
    SETTINGS_MENU = "settings_menu"
    
    # NPC 交互菜單
    CRYSTAL_MENU = "crystal_menu"
    ALCHEMY_MENU = "alchemy_menu"
    DUNGEON_MENU = "dungeon_menu"
    
    # 玩家菜單
    STAT_MENU = "stat_menu"
    SKILL_CHAIN_MENU = "skill_chain_menu"
    SKILL_LIBRARY_MENU = "skill_library_menu"
    SKILL_CHAIN_EDIT_MENU = "skill_chain_edit_menu"
    
    # 選擇菜單
    ELEMENT_MENU = "element_menu"
    ELEMENT_CHOOSE_MENU = "element_choose_menu"
    AMPLIFIER_MENU = "amplifier_menu"
    AMPLIFIER_CHOOSE_MENU = "amplifier_choose_menu"
    AMPLIFIER_STAT_MENU = "amplifier_stat_menu"
    MAIN_MATERIAL_MENU = "main_material_menu"
    
    # 輔助菜單
    NAMING_MENU = "naming_menu"


# ============================================================================
# 各菜單專屬動作類
# ============================================================================

class MainMenuAction(str, Enum):
    """主菜單專屬動作"""
    ENTER_LOBBY = "enter_lobby"
    SHOW_SETTINGS = "show_setting"
    EXIT_GAME = "exit"


class StatMenuAction(str, Enum):
    """屬性菜單專屬動作"""
    UPGRADE_ATTACK = "upgrade_attack"
    UPGRADE_DEFENSE = "upgrade_defense"
    UPGRADE_MOVEMENT = "upgrade_movement"
    UPGRADE_HEALTH = "upgrade_health"
    BACK_TO_CRYSTAL = "crystal_menu"


class AlchemyMenuAction(str, Enum):
    """煉金菜單專屬動作"""
    SELECT_MAIN_MATERIAL = "select_main_material"
    SELECT_ELEMENT = "select_element"
    SELECT_AMPLIFIER = "select_amplifier"
    CRAFT_SKILL = "craft_skill"
    CONFIRM_CRAFT = "confirm_craft"
    RESET = "reset"
    BACK = "back"


class CrystalMenuAction(str, Enum):
    """魔法水晶菜單專屬動作"""
    AWAKEN_ELEMENT = "awaken_element"
    UPGRADE_STATS = "upgrade_stats"
    VIEW_ELEMENTS = "view_elements"
    BACK = "back"


class DungeonMenuAction(str, Enum):
    """副本菜單專屬動作"""
    SELECT_DUNGEON = "select_dungeon"
    ENTER_DUNGEON = "enter_dungeon"
    VIEW_DUNGEON_INFO = "view_dungeon_info"
    BACK = "back"


class ElementMenuAction(str, Enum):
    """元素菜單專屬動作"""
    SELECT_FIRE = "element_fire"
    SELECT_WATER = "element_water"
    SELECT_EARTH = "element_earth"
    SELECT_WIND = "element_wind"
    SELECT_LIGHT = "element_light"
    SELECT_DARK = "element_dark"
    CONFIRM_SELECTION = "confirm_element"
    BACK = "back"


class AmplifierMenuAction(str, Enum):
    """增幅器菜單專屬動作"""
    SELECT_DAMAGE = "amplifier_damage"
    SELECT_PENETRATION = "amplifier_penetration"
    SELECT_REDUCTION = "amplifier_reduction"
    SELECT_DODGE = "amplifier_dodge"
    SELECT_CRITICAL = "amplifier_critical"
    CONFIRM_SELECTION = "confirm_amplifier"
    BACK = "back"


class SkillChainMenuAction(str, Enum):
    """技能鏈菜單專屬動作"""
    EDIT_CHAIN = "edit_skill_chain"
    CREATE_CHAIN = "create_skill_chain"
    DELETE_CHAIN = "delete_skill_chain"
    SWITCH_CHAIN = "switch_skill_chain"
    BACK = "back"


class SkillChainEditMenuAction(str, Enum):
    """技能鏈編輯菜單專屬動作"""
    ADD_SKILL = "add_skill_to_chain"
    REMOVE_SKILL = "remove_skill_from_chain"
    MOVE_SKILL_UP = "move_skill_up"
    MOVE_SKILL_DOWN = "move_skill_down"
    SAVE_CHAIN = "save_skill_chain"
    CANCEL_EDIT = "cancel_edit"


class SkillLibraryMenuAction(str, Enum):
    """技能庫菜單專屬動作"""
    SELECT_SKILL = "select_skill"
    VIEW_SKILL_DETAILS = "view_skill_details"
    DELETE_SKILL = "delete_skill"
    SORT_BY_NAME = "sort_by_name"
    SORT_BY_ELEMENT = "sort_by_element"
    SORT_BY_TYPE = "sort_by_type"
    BACK = "back"


class SettingsMenuAction(str, Enum):
    """設置菜單專屬動作"""
    TOGGLE_SOUND = "toggle_sound"
    TOGGLE_MUSIC = "toggle_music"
    ADJUST_VOLUME = "adjust_volume"
    CHANGE_RESOLUTION = "change_resolution"
    TOGGLE_FULLSCREEN = "toggle_fullscreen"
    RESET_SETTINGS = "reset_settings"
    BACK = "back"


# ============================================================================
# 菜單結果數據類
# ============================================================================

@dataclass
class MenuResult:
    """菜單操作結果的標準化數據類"""
    action: str  # 動作名稱（可以是任何 Action 枚舉值）
    success: bool = True  # 操作是否成功
    data: Optional[Dict[str, Any]] = None  # 附加數據
    message: Optional[str] = None  # 提示訊息
    next_menu: Optional[str] = None  # 下一個要打開的菜單名稱
    close_current: bool = False  # 是否關閉當前菜單
    
    def __str__(self) -> str:
        """返回動作字符串（用於向後兼容）"""
        return self.action
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'action': self.action,
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'next_menu': self.next_menu,
            'close_current': self.close_current
        }


@dataclass
class MenuConfig:
    """菜單配置的標準化數據類"""
    name: str  # 菜單名稱
    title: str  # 菜單標題
    closable: bool = True  # 是否可關閉
    modal: bool = False  # 是否為模態菜單（阻止下層菜單接收事件）
    overlay_alpha: int = 200  # 遮罩透明度 (0-255)
    overlay_color: tuple = (0, 0, 0)  # 遮罩顏色
    position: Optional[tuple] = None  # 菜單位置 (x, y)，None 表示居中
    size: Optional[tuple] = None  # 菜單大小 (width, height)，None 表示自動
    font_size: int = 48  # 標題字體大小
    button_font_size: int = 36  # 按鈕字體大小
    init_data: Optional[Dict[str, Any]] = None  # 初始化數據
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'name': self.name,
            'title': self.title,
            'closable': self.closable,
            'modal': self.modal,
            'overlay_alpha': self.overlay_alpha,
            'overlay_color': self.overlay_color,
            'position': self.position,
            'size': self.size,
            'font_size': self.font_size,
            'button_font_size': self.button_font_size,
            'init_data': self.init_data
        }


# 預定義的菜單配置
MENU_CONFIGS = {
    'main_menu': MenuConfig(
        name='main_menu',
        title='Main Menu',
        closable=False,
        modal=True
    ),
    'stat_menu': MenuConfig(
        name='stat_menu',
        title='Stat Upgrade',
        closable=True,
        modal=False
    ),
    'alchemy_menu': MenuConfig(
        name='alchemy_menu',
        title='Skill Crafting',
        closable=True,
        modal=False
    ),
    'crystal_menu': MenuConfig(
        name='crystal_menu',
        title='Magic Crystal',
        closable=True,
        modal=False
    ),
    'dungeon_menu': MenuConfig(
        name='dungeon_menu',
        title='Dungeon Portal',
        closable=True,
        modal=False
    ),
    'element_menu': MenuConfig(
        name='element_menu',
        title='Element Selection',
        closable=True,
        modal=False
    ),
    'amplifier_menu': MenuConfig(
        name='amplifier_menu',
        title='Amplifier Selection',
        closable=True,
        modal=False
    ),
    'skill_chain_menu': MenuConfig(
        name='skill_chain_menu',
        title='Skill Chains',
        closable=True,
        modal=False
    ),
    'skill_library_menu': MenuConfig(
        name='skill_library_menu',
        title='Skill Library',
        closable=True,
        modal=False
    ),
    'settings_menu': MenuConfig(
        name='settings_menu',
        title='Settings',
        closable=True,
        modal=True
    ),
}


def get_menu_config(menu_name: str) -> MenuConfig:
    """
    獲取菜單配置
    
    Args:
        menu_name: 菜單名稱
        
    Returns:
        MenuConfig: 菜單配置對象，如果不存在則返回默認配置
    """
    return MENU_CONFIGS.get(menu_name, MenuConfig(
        name=menu_name,
        title=menu_name.replace('_', ' ').title()
    ))


def create_menu_result(
    action: str,
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    next_menu: Optional[str] = None,
    close_current: bool = False
) -> MenuResult:
    """
    創建標準化的菜單結果
    
    Args:
        action: 動作名稱
        success: 是否成功
        data: 附加數據
        message: 提示訊息
        next_menu: 下一個菜單
        close_current: 是否關閉當前菜單
        
    Returns:
        MenuResult: 菜單結果對象
    """
    return MenuResult(
        action=action,
        success=success,
        data=data,
        message=message,
        next_menu=next_menu,
        close_current=close_current
    )


# 常用的菜單結果快捷方式
def back_result(message: Optional[str] = None) -> MenuResult:
    """返回上一級菜單"""
    return MenuResult(
        action=MenuAction.BACK,
        close_current=True,
        message=message
    )


def confirm_result(data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> MenuResult:
    """確認操作"""
    return MenuResult(
        action=MenuAction.CONFIRM,
        data=data,
        message=message
    )


def cancel_result(message: Optional[str] = None) -> MenuResult:
    """取消操作"""
    return MenuResult(
        action=MenuAction.CANCEL,
        close_current=True,
        message=message
    )


def navigate_result(next_menu: str, close_current: bool = False, data: Optional[Dict[str, Any]] = None) -> MenuResult:
    """導航到另一個菜單"""
    return MenuResult(
        action=f"navigate_to_{next_menu}",
        next_menu=next_menu,
        close_current=close_current,
        data=data
    )


def error_result(message: str, data: Optional[Dict[str, Any]] = None) -> MenuResult:
    """錯誤結果"""
    return MenuResult(
        action="error",
        success=False,
        message=message,
        data=data
    )


# ============================================================================
# 菜單動作輔助類 - 簡化菜單切換和動作創建
# ============================================================================

class MenuActionHelper:
    """菜單動作輔助類 - 提供便捷的菜單操作方法"""
    
    @staticmethod
    def navigate_to(menu_name: str, close_current: bool = True, data: Optional[Dict[str, Any]] = None) -> MenuResult:
        """
        導航到指定菜單
        
        Args:
            menu_name: 目標菜單名稱
            close_current: 是否關閉當前菜單（默認 True）
            data: 傳遞給目標菜單的數據
            
        Returns:
            MenuResult: 導航結果
        """
        return MenuResult(
            action=f"navigate_to_{menu_name}",
            next_menu=menu_name,
            close_current=close_current,
            data=data
        )
    
    @staticmethod
    def switch_menu(from_menu: str, to_menu: str, data: Optional[Dict[str, Any]] = None) -> MenuResult:
        """
        從一個菜單切換到另一個菜單（關閉當前，打開新的）
        
        Args:
            from_menu: 當前菜單名稱
            to_menu: 目標菜單名稱
            data: 傳遞給目標菜單的數據
            
        Returns:
            MenuResult: 切換結果
        """
        return MenuResult(
            action=f"switch_from_{from_menu}_to_{to_menu}",
            next_menu=to_menu,
            close_current=True,
            data=data
        )
    
    @staticmethod
    def overlay_menu(base_menu: str, overlay_menu: str, data: Optional[Dict[str, Any]] = None) -> MenuResult:
        """
        在當前菜單上疊加新菜單（不關閉當前菜單）
        
        Args:
            base_menu: 基礎菜單名稱
            overlay_menu: 要疊加的菜單名稱
            data: 傳遞給疊加菜單的數據
            
        Returns:
            MenuResult: 疊加結果
        """
        return MenuResult(
            action=f"overlay_{overlay_menu}_on_{base_menu}",
            next_menu=overlay_menu,
            close_current=False,
            data=data
        )
    
    @staticmethod
    def action_with_navigation(
        action: str,
        success: bool = True,
        message: Optional[str] = None,
        next_menu: Optional[str] = None,
        close_current: bool = False,
        data: Optional[Dict[str, Any]] = None
    ) -> MenuResult:
        """
        創建帶導航的動作結果（執行動作後可選擇性導航）
        
        Args:
            action: 動作名稱
            success: 是否成功
            message: 提示訊息
            next_menu: 下一個菜單（可選）
            close_current: 是否關閉當前菜單
            data: 附加數據
            
        Returns:
            MenuResult: 動作結果
        """
        return MenuResult(
            action=action,
            success=success,
            message=message,
            next_menu=next_menu,
            close_current=close_current,
            data=data
        )


# ============================================================================
# 向後兼容性支持
# ============================================================================

# 為了向後兼容，創建 MenuAction 別名指向 BasicAction
MenuAction = BasicAction

# 導出所有 Action 類的字典，方便動態訪問
MENU_ACTION_CLASSES = {
    'basic': BasicAction,
    'navigation': MenuNavigation,
    'main_menu': MainMenuAction,
    'stat_menu': StatMenuAction,
    'alchemy_menu': AlchemyMenuAction,
    'crystal_menu': CrystalMenuAction,
    'dungeon_menu': DungeonMenuAction,
    'element_menu': ElementMenuAction,
    'amplifier_menu': AmplifierMenuAction,
    'skill_chain_menu': SkillChainMenuAction,
    'skill_chain_edit_menu': SkillChainEditMenuAction,
    'skill_library_menu': SkillLibraryMenuAction,
    'settings_menu': SettingsMenuAction,
}


def get_action_class(menu_name: str):
    """
    根據菜單名稱獲取對應的 Action 類
    
    Args:
        menu_name: 菜單名稱
        
    Returns:
        對應的 Action 枚舉類，如果不存在則返回 BasicAction
    """
    return MENU_ACTION_CLASSES.get(menu_name, BasicAction)
