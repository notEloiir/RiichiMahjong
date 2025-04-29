

class Player:
    def __init__(self, is_human=False, model=None):
        self.is_human: bool = is_human
        self.model = model
