import pygame
import gui.ui as ui
import gui.board as board


class Menu:
    def __init__(self, gui):
        self.gui = gui
        self.display_surface = self.gui.display_surface
        self.width, self.height = self.display_surface.get_size()
        
        self.play_button = ui.Button(
            position=(0.3 * self.width, 0.1 * self.height),
            size=(0.4 * self.width, 0.23 * self.height),
            on_click=lambda: self.gui.switch_game_screen(board.Board(self.gui)),
            text="Play",
        )
        self.settings_button = ui.Button(
            position=(0.3 * self.width, 0.38 * self.height),
            size=(0.4 * self.width, 0.23 * self.height),
            on_click=lambda: print("settings"),
            text="Settings",
        )
        self.exit_button = ui.Button(
            position=(0.3 * self.width, 0.66 * self.height),
            size=(0.4 * self.width, 0.23 * self.height),
            on_click=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
            text="Exit",
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.play_button.handle_click(event.pos)
            self.settings_button.handle_click(event.pos)
            self.exit_button.handle_click(event.pos)

    def draw(self) -> None:
        self.display_surface.fill("#8CBEB2")
        
        self.play_button.draw(self.display_surface)
        self.settings_button.draw(self.display_surface)
        self.exit_button.draw(self.display_surface)