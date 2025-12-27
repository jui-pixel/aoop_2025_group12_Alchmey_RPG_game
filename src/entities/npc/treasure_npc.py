from .base_npc_facade import AbstractNPCFacade
from src.menu.menu_config import MenuNavigation
from src.ecs.components import TreasureStateComponent

class TreasureNPC(AbstractNPCFacade):
    """
    寶藏 NPC 門面。
    交互後開啟幸運轉盤。
    """
    def __init__(self, game, ecs_entity: int):
        super().__init__(game, ecs_entity)
        
        interact_comp = self._get_interact_comp()
        interact_comp.tag = "treasure_npc"
        interact_comp.start_interaction = self.start_interaction

    def start_interaction(self) -> None:
        """開啟轉盤菜單"""
        # 1. 獲取狀態組件
        # 假設你的 world 是 self.game.world
        try:
            treasure_state = self.game.world.component_for_entity(self.ecs_entity, TreasureStateComponent)
        except KeyError:
            # 防呆：如果忘記加組件，就臨時補一個
            treasure_state = TreasureStateComponent()
            self.game.world.add_component(self.ecs_entity, treasure_state)

        # 2. 檢查是否已經轉過
        if treasure_state.is_looted:
            print("Treasure NPC: 'You have already tested your luck!'")
            # 這裡可以改成顯示一個對話框 Messagebox
            self._get_interact_comp().is_interacting = False
            return

        # 3. 準備開啟菜單
        comp = self._get_interact_comp()
        comp.is_interacting = True
        
        # 定義回調函數：當轉盤結束時執行
        def on_spin_finished():
            treasure_state.is_looted = True
            print(f"NPC {self.ecs_entity} marked as looted.")

        if self.game and self.game.menu_manager:
            # 動態註冊/獲取菜單
            # 注意：這裡我們需要每次都將 callback 傳進去，或者重新建立 Menu 實例
            # 為了簡單起見，我們可以在這裡重新實例化 Menu，或者給 Menu 加一個 set_callback 方法
            # 這裡示範重新實例化，確保狀態乾淨
            from src.menu.menus.treasure_menu import TreasureMenu
            
            menu = TreasureMenu(self.game, on_spin_callback=on_spin_finished)
            
            self.game.menu_manager.register_menu(
                MenuNavigation.TREASURE_MENU, 
                menu,
                update=True
            )
            
            self.game.menu_manager.open_menu(MenuNavigation.TREASURE_MENU)

    def end_interaction(self) -> None:
        comp = self._get_interact_comp()
        comp.is_interacting = False
        if self.game and self.game.menu_manager:
            self.game.menu_manager.set_menu(None)