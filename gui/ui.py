import pygame
import gui.settings as settings


class UIItem:
    def __init__(self, position=(0, 0), size=(0, 0)) -> None:
        self.size = size
        self.position = position
        self.rect = pygame.rect.Rect(*self.position, *self.size)
        
    def draw(self, display_surface):
        raise NotImplementedError("Method draw is not implemented!")


class Label(UIItem):
    def __init__(
        self,
        position=(0, 0),
        size=(0, 0),
        rotation=0,
        text="",
        text_color=settings.PRIMARY_COLOR,
        align="center",
    ) -> None:
        super().__init__(position, size)
        self.rotation = rotation
        self.text = text
        self.text_color = text_color
        self.align = align

    def draw(self, display_surface):
        lines_no = self.text.count("\n") + 1

        if self.text:
            font = pygame.font.Font(settings.FONT_NAME, int(self.size[1]) // (2 * lines_no))
            text = font.render(self.text, True, self.text_color)
            if self.align == "left":
                text_position = (
                    0,
                    (self.size[1] / 2 - text.get_height() / 2),
                )
            elif self.align == "right":
                text_position = (
                    self.size[0] - text.get_width(),
                    (self.size[1] / 2 - text.get_height() / 2),
                )
            else:
                text_position = (
                    (self.size[0] / 2 - text.get_width() / 2),
                    (self.size[1] / 2 - text.get_height() / 2),
                )
            rotated_text = pygame.transform.rotate(text, 90 * self.rotation)
            if self.rotation == 0:
                rotated_rect = rotated_text.get_rect(
                    topleft=(
                        self.position[0] + text_position[0],
                        self.position[1] + text_position[1],
                    )
                )
            elif self.rotation == 1:
                rotated_rect = rotated_text.get_rect(
                    bottomleft=(
                        self.position[0] + text_position[1],
                        self.position[1] - text_position[0],
                    )
                )
            elif self.rotation == 2:
                rotated_rect = rotated_text.get_rect(
                    bottomright=(
                        self.position[0] - text_position[0],
                        self.position[1] - text_position[1],
                    )
                )
            elif self.rotation == 3:
                rotated_rect = rotated_text.get_rect(
                    topright=(
                        self.position[0] - text_position[1],
                        self.position[1] + text_position[0],
                    )
                )
            display_surface.blit(rotated_text, rotated_rect)


class Button(UIItem):
    def __init__(
        self,
        position=(0, 0),
        size=(0, 0),
        on_click=lambda: ...,
        text="",
        text_color=settings.PRIMARY_COLOR,
        bg_color=settings.SECONDARY_COLOR,
    ):
        super().__init__(position, size)

        self.on_click = on_click

        self.text_color = text_color
        self.bg_color = bg_color

        self.label = Label(
            position=self.position,
            size=self.size,
            text=text,
        )

    def draw(self, display_surface):
        rect = pygame.rect.Rect(*self.position, *self.size)
        pygame.draw.rect(display_surface, self.bg_color, rect, 0, 10)

        self.label.draw(display_surface)

    def handle_click(self, mouse_pos):
        rect = pygame.rect.Rect(*self.position, *self.size)
        if rect.collidepoint(*mouse_pos):
            self.on_click()


class YesOrNoPopUp(UIItem):
    def __init__(
        self,
        position=(0, 0),
        size=(0, 0),
        on_yes=None,
        on_no=None,
        yes_text="",
        no_text="",
        pop_up_text="",
        text_color=settings.PRIMARY_COLOR,
        bg_color=settings.SECONDARY_COLOR,
    ):
        super().__init__(position, size)

        self.active = False

        self.text_color = text_color
        self.bg_color = bg_color

        self.label = Label(
            position=self.position,
            size=(self.size[0], self.size[1] // 2),
            text=pop_up_text,
            text_color=self.text_color,
        )

        self.yes_button = Button(
            (self.position[0] + 0.1 * self.size[0], self.position[1] + 0.6 * self.size[1]),
            (0.35 * self.size[0], 0.3 * self.size[1]),
            on_click=on_yes,
            text=yes_text,
            bg_color="#8CBEB2",
            text_color=self.text_color,
        )
        self.no_button = Button(
            (self.position[0] + 0.55 * self.size[0], self.position[1] + 0.6 * self.size[1]),
            (0.35 * self.size[0], 0.3 * self.size[1]),
            on_click=on_no,
            text=no_text,
            bg_color="#F3B562",
            text_color=self.text_color,
        )



    def draw(self, display_surface):
        if not self.active:
            return

        pygame.draw.rect(display_surface, self.bg_color, self.rect, 0, 10)

        self.label.draw(display_surface)
        self.yes_button.draw(display_surface)
        self.no_button.draw(display_surface)

    def toggle(self):
        self.active = not self.active

    def handle_click(self, mouse_pos):
        if not self.active:
            return
        
        if not self.rect.collidepoint(*mouse_pos):
            self.active = False
            return

        self.yes_button.handle_click(mouse_pos)
        self.no_button.handle_click(mouse_pos)
