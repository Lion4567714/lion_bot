### PARENT CLASS ###
class Response: 
    piety: int

    def __init__(self, piety: int = -1):
        self.piety = piety


### CHILD CLASSES ###
class Silent(Response):
    def __init__(self):
        super().__init__()


class Message(Response):
    content: str

    def __init__(self, content: str = ''):
        super().__init__()
        self.content = content


class Reply(Message): 
    def __init__(self):
        super().__init__()


class Reaction(Response):
    emoji: str
    piety: int

    def __init__(self, emoji: str, piety: int = -1):
        super().__init__(piety)
        self.emoji = emoji
