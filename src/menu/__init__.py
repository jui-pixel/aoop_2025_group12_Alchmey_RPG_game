# 1. 匯入基礎抽象類與通用組件
from .abstract_menu import AbstractMenu
from .button import Button

# 2. 匯入所有具體選單類別 (根據您的檔案結構命名)
from .menus.alchemy_menu import AlchemyMenu
from .menus.amplifier_choose_menu import AmplifierChooseMenu
from .menus.amplifier_menu import AmplifierMenu
from .menus.amplifier_stat_menu import AmplifierStatMenu
from .menus.crystal_menu import CrystalMenu
from .menus.dungeon_menu import DungeonMenu
from .menus.element_choose_menu import ElementChooseMenu
from .menus.element_menu import ElementMenu
from .menus.main_material_menu import MainMaterialMenu
from .menus.main_menu import MainMenu
from .menus.naming_menu import NamingMenu
from .menus.settings_menu import SettingsMenu
from .menus.skill_chain_edit_menu import SkillChainEditMenu
from .menus.skill_chain_menu import SkillChainMenu
from .menus.skill_library_menu import SkillLibraryMenu
from .menus.stat_menu import StatMenu
from .menus.win_menu import WinMenu

from .menu_config import MenuNavigation, BasicAction
# 3. 定義公開接口，方便使用 from module import *
__all__ = [
    'AbstractMenu',
    'Button',
    'AlchemyMenu',
    'AmplifierChooseMenu',
    'AmplifierMenu',
    'AmplifierStatMenu',
    'CrystalMenu',
    'DungeonMenu',
    'ElementChooseMenu',
    'ElementMenu',
    'MainMaterialMenu',
    'MainMenu',
    'NamingMenu',
    'SettingsMenu',
    'SkillChainEditMenu',
    'SkillChainMenu',
    'SkillLibraryMenu',
    'StatMenu',
    'WinMenu',
    'MenuNavigation',
    'BasicAction',
]