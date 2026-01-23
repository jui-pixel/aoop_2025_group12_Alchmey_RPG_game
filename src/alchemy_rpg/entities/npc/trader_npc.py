from .base_npc_facade import AbstractNPCFacade
from src.menu.menu_config import MenuNavigation

class TraderNPC(AbstractNPCFacade):
    """
    商人 NPC 門面 (Facade)。
    負責開啟交易菜單。
    """
    def __init__(self, game, ecs_entity: int):
        super().__init__(game, ecs_entity)
        
        # 綁定交互邏輯
        interact_comp = self._get_interact_comp()
        interact_comp.tag = "trader_npc"
        interact_comp.start_interaction = self.start_interaction

    def start_interaction(self) -> None:
        """開啟交易菜單"""
        comp = self._get_interact_comp()
        comp.is_interacting = True
        
        # 確保 MenuManager 已註冊 TraderMenu
        if self.game and self.game.menu_manager:
            # 如果尚未註冊，這裡可以動態註冊 (或在 Game 初始化時註冊)
            if not self.game.menu_manager.menus.get(MenuNavigation.TRADER_MENU):
                from src.menu.menus.trader_menu import TraderMenu
                self.game.menu_manager.register_menu(
                    MenuNavigation.TRADER_MENU, 
                    TraderMenu(self.game)
                )
            
            self.game.menu_manager.open_menu(MenuNavigation.TRADER_MENU)
        
        print("Trader NPC: 'Health is wealth, my friend. But Mana buys Health.'")

    def end_interaction(self) -> None:
        """關閉交易菜單"""
        comp = self._get_interact_comp()
        comp.is_interacting = False
        if self.game and self.game.menu_manager:
            self.game.menu_manager.set_menu(None)