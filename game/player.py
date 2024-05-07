from train_models.models import MahjongNN
from typing import Optional


class Player:
    def __init__(self, is_human=False, model=None):
        self.is_human: bool = is_human
        self.model: Optional[MahjongNN] = model
