# src/menu/menu_config.py
"""
菜單配置模組 - 統一管理菜單的回傳動作、參數和配置
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class MenuAction(str, Enum):
    """標準菜單動作枚舉"""
    # 通用動作
    BACK = "BACK"
    EXIT_MENU = "EXIT_MENU"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"
    CONFIRM_CLOSE = "CONFIRM_CLOSE"
    
    # 導航動作
    ENTER_LOBBY = "enter_lobby"
    SHOW_SETTING = "show_setting"
    EXIT_GAME = "exit"
    
    # 菜單切換動作
    SHOW_MAIN_MENU = "main_menu"
    SHOW_CRYSTAL_MENU = "crystal_menu"
    SHOW_STAT_MENU = "stat_menu"
    SHOW_ALCHEMY_MENU = "alchemy_menu"
    SHOW_DUNGEON_MENU = "dungeon_menu"
    SHOW_ELEMENT_MENU = "element_menu"
    SHOW_AMPLIFIER_MENU = "amplifier_menu"
    SHOW_SKILL_CHAIN_MENU = "skill_chain_menu"
    SHOW_SKILL_LIBRARY_MENU = "skill_library_menu"
    SHOW_SETTINGS_MENU = "settings_menu"
    
    # 主材料選擇動作
    SELECT_MAIN_MATERIAL = "select_main_material"
    MAIN_MATERIAL_MISSILE = "main_material_missile"
    MAIN_MATERIAL_SHIELD = "main_material_shield"
    MAIN_MATERIAL_CLOTH = "main_material_cloth"
    
    # 元素選擇動作
    SELECT_ELEMENT = "select_element"
    ELEMENT_FIRE = "element_fire"
    ELEMENT_WATER = "element_water"
    ELEMENT_EARTH = "element_earth"
    ELEMENT_WIND = "element_wind"
    
    # 增幅器選擇動作
    SELECT_AMPLIFIER = "select_amplifier"
    AMPLIFIER_DAMAGE = "amplifier_damage"
    AMPLIFIER_PENETRATION = "amplifier_penetration"
    AMPLIFIER_REDUCTION = "amplifier_reduction"
    AMPLIFIER_DODGE = "amplifier_dodge"
    
    # 屬性升級動作
    UPGRADE_ATTACK = "upgrade_attack"
    UPGRADE_DEFENSE = "upgrade_defense"
    UPGRADE_MOVEMENT = "upgrade_movement"
    UPGRADE_HEALTH = "upgrade_health"
    
    # 煉金動作
    CRAFT_SKILL = "craft_skill"
    CONFIRM_CRAFT = "confirm_craft"
    
    # 技能鏈動作
    EDIT_SKILL_CHAIN = "edit_skill_chain"
    SAVE_SKILL_CHAIN = "save_skill_chain"
    ADD_SKILL_TO_CHAIN = "add_skill_to_chain"
    REMOVE_SKILL_FROM_CHAIN = "remove_skill_from_chain"
    
    # 副本動作
    ENTER_DUNGEON = "enter_dungeon"
    SELECT_DUNGEON = "select_dungeon"


@dataclass
class MenuResult:
    """菜單操作結果的標準化數據類"""
    action: str  # 動作名稱（可以是 MenuAction 枚舉值）
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
