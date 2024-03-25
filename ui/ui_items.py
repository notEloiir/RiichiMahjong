import pygame, settings


class UIItem:
    def __init__(self, position, size) -> None:
        self.position = position
        self.size = size

    def draw(self, dt, display_surface):
        raise NotImplementedError("Method draw is not implemented!")


class Button(UIItem):
    def __init__(
        self,
        position,
        size,
        on_click,
        text="",
        text_color=settings.PRIMARY_COLOR,
        bg_color=settings.SECONDARY_COLOR,
    ):
        super().__init__(position, size)
        self.on_click = on_click
        self.bg_color = bg_color
        self.text = text
        self.text_color = text_color

    def draw(self, dt, display_surface):
        rect = pygame.rect.Rect(*self.position, *self.size)
        pygame.draw.rect(display_surface, self.bg_color, rect, 0, 10)

        if self.text:
            font = pygame.font.Font(settings.FONT_NAME, int(self.size[1]) // 2)
            text = font.render(self.text, True, self.text_color)
            display_surface.blit(
                text,
                (
                    self.position[0] + (self.size[0] / 2 - text.get_width() / 2),
                    self.position[1] + (self.size[1] / 2 - text.get_height() / 2),
                ),
            )

    def handle_click(self, mouse_pos):
        rect = pygame.rect.Rect(*self.position, *self.size)
        if rect.collidepoint(*mouse_pos):
            self.on_click()


class TextPopUp(UIItem):
    def __init__(
        self,
        position,
        size,
        buttons=[],
        text="",
        text_color=settings.PRIMARY_COLOR,
        bg_color=settings.SECONDARY_COLOR,
    ) -> None:
        super().__init__(position, size)
        self.active = False
        self.buttons = buttons
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color

    def draw(self, dt, display_surface):
        if not self.active:
            return

        rect = pygame.rect.Rect(*self.position, *self.size)
        pygame.draw.rect(display_surface, self.bg_color, rect, 0, 10)

        if self.text:
            font = pygame.font.Font(settings.FONT_NAME, int(0.5 * self.size[1]) // 2)
            text = font.render(self.text, True, self.text_color)
            display_surface.blit(
                text,
                (
                    self.position[0] + (self.size[0] / 2 - text.get_width() / 2),
                    self.position[1] + (0.7 * self.size[1] / 2 - text.get_height() / 2),
                ),
            )

        if self.buttons:
            ...

    def toggle(self):
        self.active = not self.active

    def handle_click(self, mouse_pos):
        rect = pygame.rect.Rect(*self.position, *self.size)
        if not rect.collidepoint(*mouse_pos):
            self.active = False
            return
        
        for button in self.buttons:
            button.handle_click(mouse_pos)
