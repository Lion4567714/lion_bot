import discord
import datetime as dt
import pytz


########### RESPONSE TYPES ############
class Response: pass


class Silent(Response):
    pass


class Message(Response):
    content: str

    def __init__(self, content: str):
        self.content = content


class Reaction(Response):
    emoji: str

    def __init__(self, emoji: str):
        self.emoji = emoji
#######################################


tracked = [
    'author.global_name',
    'author.name',
    'author.nick',
    'content',
    'channel.name',
    'created_at',
    'edited_at',
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


class MessageProcessor:
    emojis = {}


    def __init__(self):
        self.read_responses()


    def read_responses(self) -> None:
        file = open('./bot/messaging/emojis', 'r')
        for line in file.read().splitlines():
            first = line.find(':') + 1
            second = line.find(':', first + 1)
            self.emojis[line[first:second]] = line
        file.close()


    def process_message(self, message: discord.Message, debug_level: int = 0) -> Response:
        message_dict = self.message_to_dict(message)
        self.print_message(message_dict, debug_level)
        response = self.get_response(message_dict)
        return response


    def message_to_dict(self, message: discord.Message) -> dict:
        output = {}
        for field in tracked:
            attr = message
            # Break attributes of attributes down one at a time
            for subfield in field.split('.'):
                attr = getattr(attr, subfield)
            output[field] = attr
        return output


    def print_message(self, message: dict, debug_level: int) -> None:
        d: dt.datetime = message['created_at']
        d = d.now(pytz.timezone('US/Eastern'))
        time_format = '%H:%M:%S'
        
        name = message['author.nick'] if message['author.nick'] != None else message['author.global_name']

        match debug_level:
            case 0: pass
            case 1: print(f"[{d.strftime(time_format)}]: {name} said \"{message['content']}\" " + 
                          f"in {message['channel.name']}, {message['guild.name']}")
        

    def get_response(self, message: dict) -> Response:
        content = str(message['content'])
        clean_message = content.lower()
        punc = ['.', ',']       
        for p in punc:
            clean_message = clean_message.replace(p, "")

        if message['author.name'] == 'brownagedon':
            return Reaction(self.emojis['steve'])
        
        return Silent()
