from enum import Enum


class Rank(Enum):
    Count = 0
    Duke = 1
    King = 2
    Emperor = 3


class Member:
    def __init__(self, arg0, arg1 = None):
        if isinstance(arg0, int):
            self.id = arg0
            self.rank = Rank.Count
            self.name = arg1
            self.gold = 0
            self.prestige = 0
            self.piety = 0
        elif isinstance(arg0, dict):
            self.id = arg0['id']
            self.rank = Rank(arg0['rank'])
            self.name = arg0['name']
            self.gold = arg0['gold']
            self.prestige = arg0['prestige']
            self.piety = arg0['piety']        


    def __str__(self):
        return f'Member({self.rank.name} {self.name}: Gold->{self.gold}, Prestige->{self.prestige}, Piety->{self.piety})'


    def print_format(self) -> str:
        output = \
f"""
> **__{self.rank.name} {self.name}__**
> <:gold:1211490700974366720> {self.gold}
> <:prestige:1211489226949001256> {self.prestige}
> <:piety:1211489458717982750> {self.piety}
"""
        return output
    

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank.value,
            'name': self.name,
            'gold': self.gold,
            'prestige': self.prestige,
            'piety': self.piety,
        }
