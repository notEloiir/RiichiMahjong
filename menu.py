import pygame, ui, board
from gui import Gui


class Menu():
    def __init__(self, gui: Gui):
        self.gui = gui
        self.setup_ui()
    
    def setup_ui(self):
        self.buttons = [
            ui.Button(
                on_click=lambda: self.gui.switch_game_screen(board.Board(self.gui)),
                text="Play",
            ),
            ui.Button(
                on_click=lambda: print("options"),
                text="Options",
            ),
            ui.Button(
                on_click=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
                text="Exit",
            ),
        ]
        self.buttons_container = ui.UIVerticalBox(
            size=self.gui.display_surface.get_size(), 
            items=self.buttons, 
            padding=(0.3, 0.1), 
            spacing=0.05
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                btn.handle_click(event.pos)

    def draw(self) -> None:
        self.gui.display_surface.fill("#8CBEB2")
        self.buttons_container.draw(self.gui.display_surface)