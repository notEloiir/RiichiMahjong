from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui_items import UIItem


class UIVerticalBox:
    def __init__(
        self,
        position: tuple[int, int],
        size: tuple[int, int],
        items: list[UIItem],
        padding: tuple[float, float] = (0, 0),
        spacing: float = 0,
    ):
        self.position = position
        self.size = size
        self.items = items
        self.padding = (padding[0] * size[0], padding[1] * size[1])
        self.spacing = size[1] * spacing

    def draw(self, display_surface):
        item_size = (
            self.size[0] - 2 * self.padding[0],
            (self.size[1] - 2 * self.padding[1] - (len(self.items) - 1) * self.spacing)
            // len(self.items),
        )

        for i, item in enumerate(self.items):
            item.position = (
                self.position[0] + self.padding[0],
                (item_size[1] + self.spacing) * i + self.padding[1],
            )
            item.size = item_size
            item.draw(display_surface)
