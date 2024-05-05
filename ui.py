import pygame, settings


class UIItem:
    def __init__(self, position=(0, 0), size=(0, 0)) -> None:
        self.size = size
        self.position = position

    def draw(self, dt, display_surface):
        raise NotImplementedError("Method draw is not implemented!")


class Label(UIItem):
    def __init__(
        self,
        position=(0, 0),
        size=(0, 0),
        text="",
        text_color=settings.PRIMARY_COLOR,
    ) -> None:
        super().__init__(position, size)
        self.text = text
        self.text_color = text_color

    def draw(self, dt, display_surface):
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
        self.content = UIVerticalBox(
            position=self.position,
            size=self.size,
        )
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        if self.text:
            self.content.items.append(
                Label(
                    text=text,
                    text_color=text_color,
                )
            )

    def draw(self, dt, display_surface):
        rect = pygame.rect.Rect(*self.position, *self.size)
        pygame.draw.rect(display_surface, self.bg_color, rect, 0, 10)

        self.content.position = self.position
        self.content.size = self.size
        self.content.draw(dt, display_surface)

    def handle_click(self, mouse_pos):
        rect = pygame.rect.Rect(*self.position, *self.size)
        if rect.collidepoint(*mouse_pos):
            self.on_click()


class TextPopUp(UIItem):
    def __init__(
        self,
        position=(0, 0),
        size=(0, 0),
        buttons=None,
        text="",
        text_color=settings.PRIMARY_COLOR,
        bg_color=settings.SECONDARY_COLOR,
    ) -> None:
        super().__init__(position, size)
        self.active = False
        self.content = UIVerticalBox(
            position=self.position,
            size=self.size,
            padding=(0.1, 0.1),
            spacing=0.1,
        )
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        if self.text:
            self.content.items.append(
                Label(
                    text=self.text,
                    text_color=self.text_color,
                )
            )
        self.buttons = buttons if buttons else []
        if self.buttons:
            self.content.items.append(
                UIHorizontalBox(
                    (0, 0),
                    (0, 0), 
                    items=self.buttons,
                    padding=(0, 0.1),
                    spacing=0.1,
                )
            )
        

    def draw(self, dt, display_surface):
        if not self.active:
            return

        rect = pygame.rect.Rect(*self.position, *self.size)
        pygame.draw.rect(display_surface, self.bg_color, rect, 0, 10)

        self.content.position = self.position
        self.content.size = self.size
        self.content.draw(dt, display_surface)

    def toggle(self):
        self.active = not self.active

    def handle_click(self, mouse_pos):
        rect = pygame.rect.Rect(*self.position, *self.size)
        if not rect.collidepoint(*mouse_pos):
            self.active = False
            return

        for button in self.buttons:
            button.handle_click(mouse_pos)


class UIVerticalBox(UIItem):
    def __init__(
        self,
        position: tuple[int, int]=(0, 0),
        size: tuple[int, int]=(0, 0),
        items: list[UIItem]=None,
        padding: tuple[float, float]=(0, 0),
        spacing: float=0,
    ):
        self.position = position
        self.size = size
        self.items = items if items else []
        self.padding = padding
        self.spacing = spacing
    
    def draw(self, dt, display_surface):
        padding = (self.padding[0] * self.size[0], self.padding[1] * self.size[1])
        spacing = self.size[1] * self.spacing
        item_size = (
            self.size[0] - 2 * padding[0],
            (self.size[1] - 2 * padding[1] - (len(self.items) - 1) * spacing)
            // len(self.items),
        )

        for i, item in enumerate(self.items):
            item.position = (
                self.position[0] + padding[0],
                self.position[1] + (item_size[1] + spacing) * i + padding[1],
            )
            item.size = item_size
            item.draw(dt, display_surface)


class UIHorizontalBox(UIItem):
    def __init__(
        self,
        position: tuple[int, int]=(0, 0),
        size: tuple[int, int]=(0, 0),
        items: list[UIItem]=None,
        padding: tuple[float, float]=(0, 0),
        spacing: float=0,
    ):
        self.position = position
        self.size = size
        self.items = items if items else []
        self.padding = padding
        self.spacing = spacing
    
    def draw(self, dt, display_surface):
        if not len(self.items):
            return
        
        padding = (self.padding[0] * self.size[0], self.padding[1] * self.size[1])
        spacing = self.size[0] * self.spacing
        item_size = (
            (self.size[0] - 2 * padding[0] - (len(self.items) - 1) * spacing)
            // len(self.items),
            self.size[1] - 2 * padding[1],
        )

        for i, item in enumerate(self.items):
            item.position = (
                self.position[0] + (item_size[0] + spacing) * i + padding[0],
                self.position[1] + padding[1],
            )
            item.size = item_size
            item.draw(dt, display_surface)