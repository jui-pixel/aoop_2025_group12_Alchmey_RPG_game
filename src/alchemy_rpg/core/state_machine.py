class StateMachine:
    """
    Manages the global state of the game (e.g., 'playing', 'menu', 'lobby', 'pause').
    """
    def __init__(self, initial_state="menu"):
        self.state = initial_state
        self.previous_state = None
    
    def change_state(self, new_state: str):
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            print(f"StateMachine: State changed {self.previous_state} -> {self.state}")
            
    def get_state(self) -> str:
        return self.state
