import game.src.gui.ui_items as ui_items
import game.src.gui.menu as menu


class Scores:
    def __init__(self, game, screen_size):
        self.width, self.height = screen_size
        self.active = False
        self.ready_to_continue = False
        self.visible = False
        self.final = False

        self.message_label = ui_items.Label(
            position=(0.1 * self.width, 0.1 * self.height),
            size=(0.9 * self.width, 0.1 * self.height),
            text="",
            align="left",
        )

        self.player_labels = []
        player_label_x = 0.1 * self.width
        player_label_y = 0.2 * self.height
        for _ in range(4):
            player_label = ui_items.Label(
                position=(player_label_x, player_label_y),
                size=(0.8 * self.width, 0.1 * self.height),
                text="",
                align="left",
            )
            player_label_y += 0.133 * self.height
            self.player_labels.append(player_label)

        self.continue_button = ui_items.Button(
            position=(0.1 * self.width, 0.8 * self.height),
            size=(0.2 * self.width, 0.1 * self.height),
            on_click=lambda: self.continue_match(),
            text="Continue",
        )
        self.show_board_button = ui_items.Button(
            position=(0.4 * self.width, 0.8 * self.height),
            size=(0.2 * self.width, 0.1 * self.height),
            on_click=lambda: self.toggle_visible(),
            text="Show board",
        )
        self.exit_button = ui_items.Button(
            position=(0.7 * self.width, 0.8 * self.height),
            size=(0.2 * self.width, 0.1 * self.height),
            on_click=lambda: game.switch_game_screen(menu.Menu(game)),
            text="Exit to menu",
        )

    def show(self, scores, scores_gained, message):
        self.message_label.text = message
        player_names = ["Player", "Bot1", "Bot2", "Bot3"]
        for i, player_label in enumerate(self.player_labels):
            player_label.text = (
                player_names[i].ljust(80, ".")
                + str(scores[i])
                + (" ({:+})".format(scores_gained[i]))
            )
        self.ready_to_continue = False
        self.active = True
        self.visible = True

    def continue_match(self):
        self.active = False
        self.visible = False
        self.ready_to_continue = True

    def toggle_visible(self):
        self.visible = not self.visible

    def handle_click(self, mouse_pos) -> None:
        self.continue_button.handle_click(mouse_pos)
        self.show_board_button.handle_click(mouse_pos)
        self.exit_button.handle_click(mouse_pos)

    def draw(self, display_surface) -> None:
        if not self.visible:
            return

        display_surface.fill("#8CBEB2")

        self.message_label.draw(display_surface)
        for player_label in self.player_labels:
            player_label.draw(display_surface)
        if not self.final:
            self.continue_button.draw(display_surface)
        self.show_board_button.draw(display_surface)
        self.exit_button.draw(display_surface)
