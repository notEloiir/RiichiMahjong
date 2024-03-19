import pygame


class GameScreen:
    def __init__(self) -> None:
        self.display_surface = pygame.display.get_surface()
    
    def handle_event(self, event):
        raise NotImplementedError("Method process_events is not implemented!")
    
    def update(self):
        raise NotImplementedError("Method update is not implemented!")