import pygame
import gui.ui as ui


class StatusBar:
    def __init__(self, position=(0, 0), size=(0, 0), rotation=0):
        self.position = position
        self.size = size
        self.rotation = rotation

        if self.rotation == 0:
            delta_x = self.size[0] / 3
            delta_y = 0
        elif self.rotation == 1:
            delta_x = 0
            delta_y = -(self.size[0] / 3)
        elif self.rotation == 2:
            delta_x = -(self.size[0] / 3)
            delta_y = 0
        elif self.rotation == 3:
            delta_x = 0
            delta_y = self.size[0] / 3


        self.wind_label = ui.Label(
            position=self.position,
            size=(
                self.size[0] / 3,
                self.size[1],
            ),
            rotation=rotation,
            align="left"
        )
        self.score_label = ui.Label(
            position=(
                self.position[0] + delta_x,
                self.position[1] + delta_y,
            ),
            rotation=rotation,
            size=(
                self.size[0] / 3,
                self.size[1],
            ),
        )
        self.special_label = ui.Label(
            position=(
                self.position[0] + 2 *delta_x,
                self.position[1] + 2 * delta_y,
            ),
            rotation=rotation,
            size=(
                self.size[0] / 3,
                self.size[1],
            ),
            align="right",
        )

    def update_status(self, wind, score, special):
        self.wind_label.text = wind
        self.score_label.text = score
        self.special_label.text = special

    def draw(self, display_surface):
        self.wind_label.draw(display_surface)
        self.score_label.draw(display_surface)
        self.special_label.draw(display_surface)

