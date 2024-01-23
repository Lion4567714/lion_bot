import discord
from functools import reduce

tracked = [
    'author.global_name',
    'author.name',
    'content',
    'channel.name',
    'guild.id',
    'guild.name',
    'id',
    'mention_everyone',
    # 'mentions',
    'pinned',
    'reactions',
    'role_mentions',
]

responses = {
    'todd': 'God bless our Lord and Saviour, Todd Howard.',

    'almost heaven': 'west virginia...',
    'blue ridge mountains': 'shenandoah river...',
    'live is old there': 'older than the trees...',
    'younger than the mountains': 'growin\' like a breeze',
    'country roads': 'take me home...',
    'to the place': 'i belong...',
    'west virginia': 'mountain mama...',
    'take me home': 'country roads.',
    'all my memories': 'gather \'round here...',
    'miners lady': 'stranger to blue water...',
    'dark and dusty': 'painted on the sky...',
    'misty taste of moonshine': 'teardrop in my eye...',
}


def message_to_dict(message: discord.Message) -> dict:
    output = {}
    for field in tracked:
        attr = message
        # Break attributes of attributes down one at a time
        for subfield in field.split('.'):
            attr = getattr(attr, subfield)
        output[field] = attr
    return output


def get_response(message: str) -> str:
    m = message.lower()
    punc = ['.', ',']
    for p in punc:
        m = m.replace(p, "")

    r = responses.get(m, "")
    return r
