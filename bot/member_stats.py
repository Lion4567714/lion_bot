from enum import Enum


class Rank(Enum):
    Count = 0
    Duke = 1
    King = 2
    Emperor = 3


prestige_levels = {
    0: '<:prestige_0:1217240658985750709>',
    1: '<:prestige_1:1217240658058674277>',
    2: '<:prestige_2:1217240657039593643>',
    3: '<:prestige_3:1217240655785496667>',
    4: '<:prestige_4:1217240654149713971>',
    5: '<:prestige_5:1217240652576850061>',
}

piety_levels = {
    0: '<:piety_0:1217240690250223726>',
    1: '<:piety_1:1217240689012641912>',
    2: '<:piety_2:1217240688064860200>',
    3: '<:piety_3:1217240686475219036>',
    4: '<:piety_4:1217240685812387991>',
    5: '<:piety_5:1217240684453564447>',
}


class Member:
    def __init__(self, arg0, arg1 = None):
        if isinstance(arg0, int):
            self.id = arg0
            self.rank = Rank.Count
            self.name = arg1
            self.title = None
            self.disposition = None
            self.gold = 0
            self.prestige_level = 0
            self.prestige = 0
            self.piety_level = 0
            self.piety = 0
        elif isinstance(arg0, dict):
            self.id = arg0['id']
            self.rank = Rank(arg0['rank'])
            self.name = arg0['name']
            self.title = arg0.setdefault('title')
            self.disposition = arg0.setdefault('disposition')
            self.gold = arg0['gold']
            # self.prestige_level = arg0.setdefault('prestige_level')
            self.prestige = arg0['prestige']
            self.prestige_level = 0 if self.prestige < 0 else int(self.prestige / 500) + 1
            # self.piety_level = arg0.setdefault('piety_level')
            self.piety = arg0['piety']
            self.piety_level = 0 if self.piety < 0 else int(self.piety / 500) + 1


    def __str__(self):
        return f'Member({self.rank.name} {self.name}: Gold->{self.gold}, Prestige->{self.prestige}, Piety->{self.piety})'


    def print_format(self) -> str:
#         output = \
# f"""
# > **{self.rank.name} {self.name}**
# > <:gold:1211490700974366720> {self.gold}
# > <:prestige:1211489226949001256> {self.prestige}
# > <:piety:1211489458717982750> {self.piety}
# """
        output = '> **'
        # First line (name and title)
        if self.rank.name != None:
            output += f'{self.rank.name} '
        output += f'{self.name}'
        if self.title != None:
            output += f' \"{self.title}\"'
        output += '**'
        # Second line (disposition)
        if self.disposition != None:
            output += f'\n> *{self.disposition}*'
        # Third line (stats)
        output += f'\n> <:gold:1211490700974366720> {self.gold}'
        output += f'\n> {prestige_levels[self.prestige_level]} {self.prestige}'
        output += f'\n> {piety_levels[self.piety_level]} {self.piety}'
        return output
    

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank.value,
            'name': self.name,
            'title': self.title,
            'disposition': self.disposition,
            'gold': self.gold,
            'prestige_level': self.prestige_level,
            'prestige': self.prestige,
            'piety_level': self.piety_level,
            'piety': self.piety,
        }
