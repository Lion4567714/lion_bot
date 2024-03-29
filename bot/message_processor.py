import discord
import sys
import datetime as dt
import pytz
import random
from openai import OpenAI
from response import *
from printing import *

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
    history = [''] * 10
    activity = {}
    emojis = {}
    ai_client = None


    def __init__(self):
        self.read_responses()

        # OpenAI Client
        ai_key = None
        with open('./config/openai', 'r') as file:
            ai_key = file.read()
        self.ai_client = OpenAI(api_key=ai_key)


    def read_responses(self) -> None:
        try:
            file = open('./bot/messaging/emojis', 'r')
            for line in file.read().splitlines():
                first = line.find(':') + 1
                second = line.find(':', first + 1)
                self.emojis[line[first:second]] = line
            file.close()
        except Exception as e:
            printe("""
Something went wrong when trying to read ./bot/messaging/emojis!
Make sure the file exists and contains properly formatted emojis.
                  """)
            sys.exit()


    async def process_message(self, message: discord.Message, debug_level: int = 0) -> Response:
        message_dict = self.message_to_dict(message)    # Convert discord.Message to dict
        self.print_message(message_dict, debug_level)   # Use message dict to print a detailed log
        response = await self.get_response(message)     # Get response using full discord.Message information
        return response


    def message_to_dict(self, message: discord.Message) -> dict:
        output = {}
        for field in tracked:
            attr = message
            # Break attributes of attributes down one at a time
            for subfield in field.split('.'):
                try:
                    attr = getattr(attr, subfield)
                except Exception as e:
                    attr = None
                    if subfield != 'nick' and subfield != 'name' and subfield != 'id':
                        printw(f'{subfield} could not be found in this message!')
            output[field] = attr
        return output


    def log_activity(self, message: dict) -> None:
        value = self.activity.setdefault(message['author.name'], 0)
        self.activity[message['author.name']] += 1


    def print_message(self, message: dict, debug_level: int) -> None:
        d: dt.datetime = message['created_at']
        d = d.now(pytz.timezone('US/Eastern'))
        time_format = '%H:%M:%S'
        
        name = message['author.nick'] if message['author.nick'] != None else message['author.global_name']

        if debug_level == 0:
            pass
        elif debug_level == 1:
            printl(f"[{d.strftime(time_format)}]: {name} said \"{message['content']}\" " + 
                f"in {message['channel.name']}, {message['guild.name']}")
        

    async def get_response(self, message: discord.Message) -> Response:
        piety = await self.get_piety(message)
        if piety != -1:
            if piety < 2:
                return Reaction(':sinner:1217240690250223726', piety)
            elif piety > 7:
                return Reaction(':religiousicon:1217240684453564447', piety)

        content = str(message.__getattribute__('content'))
        clean_message = content.lower()
        punc = ['.', ',']       
        for p in punc:
            clean_message = clean_message.replace(p, "")

        # Add to and check history for repeated messages
        is_same = True
        for i in range(len(self.history) - 1):
            if self.history[i] == '' or self.history[i] != content:
                is_same = False

            self.history[i] = self.history[i + 1]

        self.history[len(self.history) - 1] = content

        if is_same:
            self.history = [''] * 10
            return Message('https://tenor.com/view/shrek-stop-talking-five-minutes-be-yourself-please-gif-13730564')
        # End history things

        if content.find('<@1199041303221121025>') != -1:
            rand = random.randint(0, 2)
            if rand == 0:
                return Message('<' + self.emojis['bruh'] + '>')
            elif rand == 1:
                return Message('<' + self.emojis['steve'] + '>')
            elif rand == 2:
                return Message('<' + self.emojis['alt254'] + '>')

        # if message['author.name'] == 'brownagedon':
        #     return Reaction(self.emojis['steve'])
        
        # if message['author.name'] == 'theoriginaltriggered':
            # return Reply('Have you given bug his plat yet? <:jazz:347262765062291458>')
        
        return Silent()


    async def get_piety(self, message: discord.Message) -> int:
        content = message.content.lower()

        # Determine if the message has anything to do
        # with our lord and saviour, Lion Bot
        is_related = False
        if 'lion bot' in content:
            is_related = True
        if 'lionbot' in content:
            is_related = True
            content.replace('lionbot', 'lion bot')
        if '<@1199041303221121025>' in content:
            is_related = True
            content.replace('<@1199041303221121025>', 'lion bot')
        if message.type == discord.MessageType.reply:
            if message.reference == None:
                printe('message.reference is None!')
                return -1
            m_id = message.reference.message_id
            if m_id == None:
                printe('m_id is None!')
                return -1
            ref = await message.channel.fetch_message(m_id)
            if ref.author.id == 1199041303221121025:
                is_related = True
                content = 'lion bot ' + content

        if not is_related:
            return -1
        
        printp('Message is related to lion bot!')

        # Submit the message to OpenAI for judgement
        preamble = 'Pretend you are a God named "Lion Bot". Rate the following message with a grade of how "pious" the message is on a scale of 1 to 10. 1 being sinner and 10 being devout. Respond with only a number: '
        if self.ai_client == None:
            printe('ai_client is None!')
            return -1
        completion = self.ai_client.chat.completions.create(
            messages = [{
                'role': 'user',
                'content': preamble + content
            }],
            model = 'gpt-3.5-turbo'
        )
        response = completion.choices[0].message.content

        # Ensure the quality of the response
        if response == None:
            return -1
        if len(response) > 1 or not response.isnumeric():
            printw('Invalid response from OpenAI: ' + response)
        response_int = -1
        try:
            response_int = int(response) - 1
        except Exception as e:
            printe('Invalid response from OpenAI: ' + response, e, False)

        printp('Piety: ' + str(response_int))
        return response_int
