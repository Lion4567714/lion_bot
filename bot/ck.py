# TODO: Introduce "update" field to keep track of whether the database needs to be updated
#       the next time something is accessed


from enum import Enum
from pymongo.collection import Collection
from printing import *


class ck:
    LEVEL_CUTOFF = 500
    PRESTIGE_ROLES = {
        0: 1223458368723882078,
        1: 1223457647601389673,
        2: 1223457640362016881,
        3: 1223457631058788402,
        4: 1223457615271694416,
        5: 1223457543800488017,
    }
    PRESTIGE_LEVELS = {
        0: '<:disgraced:1217240658985750709>',
        1: '<:established:1217240658058674277>',
        2: '<:distinguished:1217240657039593643>',
        3: '<:illustrious:1217240655785496667>',
        4: '<:exaltedamongmen:1217240654149713971>',
        5: '<:thelivinglegend:1217240652576850061>',
    }
    PIETY_LEVELS = {
        0: '<:sinner:1217240690250223726>',
        1: '<:dutiful:1217240689012641912>',
        2: '<:faithful:1217240688064860200>',
        3: '<:devotedservant:1217240686475219036>',
        4: '<:paragonofvirtue:1217240685812387991>',
        5: '<:religiousicon:1217240684453564447>',
    }


    class Member:
        class Rank(Enum):
            Count = 0
            Duke = 1
            King = 2
            Emperor = 3


        uid: int

        rank: Rank
        name: str
        title: str
        disposition: str

        gold: float
        gold_income: float

        prestige: float
        prestige_level: int
        prestige_income: float

        piety: float
        piety_level: int
        piety_income: float


        def to_level(self, amount: float) -> int:
            return 0 if amount < 0 else min(int(amount / ck.LEVEL_CUTOFF) + 1, 5)


        def increment_gold(self, amount: float) -> None:
            self.gold = round(self.gold + amount)


        def increment_prestige(self, amount: float) -> None:
            new_amount = round(self.prestige + amount, 1)
            before = self.to_level(self.prestige)
            after = self.to_level(new_amount)
            if before != after:
                self.prestige_level = after
            self.prestige = new_amount


        def increment_piety(self, amount: float) -> None:
            new_amount = round(self.piety + amount, 1)
            before = self.to_level(self.piety)
            after = self.to_level(new_amount)
            if before != after:
                self.piety_level = after
            self.piety = new_amount


        def add_income(self) -> None:
            self.increment_gold(self.gold_income)
            self.increment_prestige(self.prestige_income)
            self.increment_piety(self.piety_income)


        def __init__(self, d: dict) -> None:
            if 'uid' not in d or 'name' not in d:
                printe('ck member dictionary is missing important information!')
                return

            self.uid = d['uid']
            self.rank = self.Rank(d.setdefault('rank', 0))
            self.name = d['name']
            self.title = d.setdefault('title', '')
            self.disposition = d.setdefault('disposition', '')
            self.gold = d.setdefault('gold', 0)
            self.gold_income = d.setdefault('gold_income', 1.0)
            self.prestige = d.setdefault('prestige', 0)
            self.prestige_level = self.to_level(self.prestige)
            self.prestige_income = d.setdefault('prestige_income', 0.2)
            self.piety = d.setdefault('piety', 0)
            self.piety_level = self.to_level(self.piety)
            self.piety_income = d.setdefault('piety_income', 0)


        def __str__(self):
            return f'Member({self.rank.name} {self.name}: Gold->{self.gold}, Prestige->{self.prestige}, Piety->{self.piety})'


        def print_format(self) -> str:
            output = '> **'

            # First line (name and title)
            if self.rank.name != None:
                output += f'{self.rank.name} '
            output += f'{self.name}'
            if self.title != '':
                output += f' \"{self.title}\"'
            output += '**'

            # Second line (disposition)
            if self.disposition != '':
                output += f'\n> *{self.disposition}*'

            # Third line (stats)
            output += f'\n> <:gold:1211490700974366720> {round(self.gold, 1)} + {self.gold_income}'
            output += f'\n> {ck.PRESTIGE_LEVELS[self.prestige_level]} {round(self.prestige, 1)} + {self.prestige_income}'
            output += f'\n> {ck.PIETY_LEVELS[self.piety_level]} {round(self.piety, 1)} + {self.piety_income}'
            
            return output
        

        def to_dict(self) -> dict:
            return {
                'uid': self.uid,
                'rank': self.rank.value,
                'name': self.name,
                'title': self.title,
                'disposition': self.disposition,
                'gold': self.gold,
                'gold_income': self.gold_income,
                'prestige': self.prestige,
                'prestige_level': self.prestige_level,
                'prestige_income': self.prestige_income,
                'piety': self.piety,
                'piety_level': self.piety_level,
                'piety_income': self.piety_income,
            }


    members: dict[int, Member]


    def __init__(self, collection: Collection) -> None:
        self.collection = collection

        self.members = {}
        member_collection: list[dict]
        member_collection = list(collection.find({}))
        for m in member_collection:
            self.members[m['uid']] = ck.Member(m)


    def backup(self, uid: int = -1) -> None:
        try:
            if uid != -1:
                self.collection.replace_one({'uid': uid}, self.members[uid].to_dict(), upsert=True)
            else:
                for uid_loop in self.members:
                    self.collection.replace_one({'uid': uid_loop}, self.members[uid_loop].to_dict(), upsert=True)
        except Exception as e:
            printe('error when trying to do a backup!', e, False)


    def add_new_member(self, member: Member) -> None:
        self.members[member.uid] = member
        # TODO: Update database


    def add_all_income(self) -> None:
        for uid in self.members:
            self.members[uid].add_income()
