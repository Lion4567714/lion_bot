from enum import Enum
import math


class Rank(Enum):
    Count = 0
    Duke = 1
    King = 2
    Emperor = 3


prestige_levels = {
    0: '<:disgraced:1217240658985750709>',
    1: '<:established:1217240658058674277>',
    2: '<:distinguished:1217240657039593643>',
    3: '<:illustrious:1217240655785496667>',
    4: '<:exaltedamongmen:1217240654149713971>',
    5: '<:thelivinglegend:1217240652576850061>',
}

piety_levels = {
    0: '<:sinner:1217240690250223726>',
    1: '<:dutiful:1217240689012641912>',
    2: '<:faithful:1217240688064860200>',
    3: '<:devotedservant:1217240686475219036>',
    4: '<:paragonofvirtue:1217240685812387991>',
    5: '<:religiousicon:1217240684453564447>',
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
            self.gold_income = 1.0
            self.prestige_level = 0
            self.prestige = 0
            self.prestige_income = 0.2
            self.piety_level = 0
            self.piety = 0
            self.piety_income = 0.0
        elif isinstance(arg0, dict):
            self.id = arg0['id']
            self.rank = Rank(arg0['rank'])
            self.name = arg0['name']
            self.title = arg0.setdefault('title')
            self.disposition = arg0.setdefault('disposition')
            self.gold = arg0['gold']
            self.gold_income = arg0.setdefault('gold_income', 1.0)
            # self.prestige_level = arg0.setdefault('prestige_level')
            self.prestige = arg0['prestige']
            self.prestige_level = 0 if self.prestige < 0 else min(int(self.prestige / 500) + 1, 5)
            self.prestige_income = arg0.setdefault('prestige_income', 0.2)
            # self.piety_level = arg0.setdefault('piety_level')
            self.piety = arg0['piety']
            self.piety_level = 0 if self.piety < 0 else min(int(self.piety / 500) + 1, 5)
            self.piety_income = arg0.setdefault('piety_income', 0.0)


    def __str__(self):
        return f'Member({self.rank.name} {self.name}: Gold->{self.gold}, Prestige->{self.prestige}, Piety->{self.piety})'


    def print_format(self) -> str:
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
        output += f'\n> <:gold:1211490700974366720> {round(self.gold, 1)} + {self.gold_income}'
        output += f'\n> {prestige_levels[self.prestige_level]} {round(self.prestige, 1)} + {self.prestige_income}'
        output += f'\n> {piety_levels[self.piety_level]} {round(self.piety, 1)} + {self.piety_income}'
        return output
    

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank.value,
            'name': self.name,
            'title': self.title,
            'disposition': self.disposition,
            'gold': self.gold,
            'gold_income': self.gold_income,
            'prestige_level': self.prestige_level,
            'prestige': self.prestige,
            'prestige_income': self.prestige_income,
            'piety_level': self.piety_level,
            'piety': self.piety,
            'piety_income': self.piety_income,
        }
