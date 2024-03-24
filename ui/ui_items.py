import pygame
import settings


class UIItem:
    def __init__(self, position, size) -> None:
        self.position = position
        self.size = size

    def draw(self, display_surface):
        raise NotImplementedError("Method draw is not implemented!")


class Button(UIItem):
    def __init__(self, position, size, bg_color, on_click, text="", text_color="black"):
        super().__init__(position, size)
        self.bg_color = bg_color
        self.text = text
        self.text_color = text_color
        self.on_click = on_click

    def draw(self, display_surface):
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
