from menu.abstract_menu import AbstractMenu

class MenuManager:
    def __init__(self, screen, game):
        self.screen = screen
        self.game = game
        self.menus = {}
        self.current_menu = None

    def register_menu(self, name, menu: AbstractMenu):
        if name in self.menus:
            pass
        self.menus[name] = menu
        menu.activate(False)

    def set_menu(self, menu_name):
        if menu_name in self.menus:
            if self.current_menu:
                self.current_menu.activate(False)
            self.current_menu = self.menus[menu_name]
            self.current_menu.activate(True)

    def draw(self):
        if self.current_menu:
            self.current_menu.draw(self.screen)

    def handle_event(self, event):
        if self.current_menu:
            return self.current_menu.handle_event(event)
        return None