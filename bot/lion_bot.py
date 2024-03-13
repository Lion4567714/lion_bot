# TODO: Track who uses /daily and how often
# TODO: Increase odds of /daily working based on social credit
# TODO: Republican bot sentiments
# TODO: Daily events
#       https://stackoverflow.com/questions/68240940/trigger-an-event-every-week-at-a-specific-day-and-time-in-discord-py


############### IMPORTS ###############
import discord
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get

import logging

import pymongo
import pymongo.errors
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import sys
import urllib.parse

import message_processor as mp
import member_stats as ms

from random import random
from random import randint
import signal
import ast
import datetime as dt

import asyncio
#######################################


############## WORK ZONE ##############

#######################################


def print_error(path: str, e: Exception, is_fatal: bool = False) -> None:
    print(f'[ERROR] Something went wrong when trying to read {path}!')
    print(e)
    if is_fatal: sys.exit()


# Load logs
mp_instance = mp.MessageProcessor()
try:
    # Activity log
    path = './bot/messaging/activity'
    file = open(path, 'r')
    mp_instance.activity = ast.literal_eval(file.read())
    file.close()
except Exception as e:
    print_error(path, e, True)


############## SIGNALS ################
def signal_handler(sig, frame):
    try:
        # Log activity
        path = './bot/messaging/activity'
        file = open(path, 'w')
        file.write(str(mp_instance.activity))
        file.close()
    except Exception as e:
        print_error(path, e, True)

    sys.exit()

signal.signal(signal.SIGINT, signal_handler)
#######################################


# Discord Client
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Logging
handler = logging.FileHandler(filename='./logs/lion_bot.log', encoding='utf-8', mode='w')

# Guilds
guild_ids = ''
try:
    path = './config/guilds'
    file = open(path, 'r')
    guild_ids = file.read().splitlines()
    file.close()
except Exception as e:
    print_error(path, e, True)

guilds = []
for guild in guild_ids:
    guilds.append(discord.Object(id=guild))


############### MONGO #################
try:
    path = './config/mongo'
    file = open(path, 'r')
    mongo = file.read().splitlines()
    file.close()
except Exception as e:
    print_error(path, e, True)

mongo_user = urllib.parse.quote(mongo[0])
mongo_pass = urllib.parse.quote(mongo[1])

uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@discordcluster.ujcowjs.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

connected_to_mongo = False
try:
    mongo_client.admin.command('ping')
    connected_to_mongo = True
    print("[STATUS] Ping successful. Connected to MongoDB!")
except Exception as e:
    print("[STATUS] Ping unsuccessful. Continuing without MongoDB...")
    # print(e)

db = mongo_client.my_database
db_posts = db['posts']
db_members = db['members']
db_daily = db['daily']
db_list = db['the list']
#######################################


############### EVENTS ################
@tasks.loop(hours = 4)
async def update_income():
    db_members.update_many({}, [
        {'$set': {'gold': {'$add': ['$gold', '$gold_income']}}},
        {'$set': {'prestige': {'$add': ['$prestige', '$prestige_income']}}},
        {'$set': {'piety': {'$add': ['$piety', '$piety_income']}}},
    ])
    print('Awarded income!')


# DM owner for errors and updates
async def message_owner(content: str) -> None:
    user = await bot.fetch_user(307723444428996608)
    await user.send(content)


@bot.event
async def on_connect():
    print(f'[STATUS] Connected to Discord as {bot.user}!')
    print("----- BEGIN LOG -----")


@bot.event
async def on_ready():
    for guild in guilds:
        await bot.tree.sync(guild=guild)

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you'))

    print(f'[STATUS] Bot is ready!')
    update_income.start()


@bot.event
async def on_message(message: discord.Message):
    post = mp_instance.message_to_dict(message)
    mp_instance.log_activity(post)

    if connected_to_mongo:
        try:
            db_posts.insert_one(post)
        except pymongo.errors.OperationFailure:
            logging.error("Something went wrong with sending a message to MongoDB!")

    if message.author == bot.user:
        return

    if random() > 0.99:
        if random() > 0.5:
            await message.channel.send('shut up')
        else:
            await message.channel.send('dumbass')

    response = mp_instance.process_message(message, 1)
    if isinstance(response, mp.Silent):
        pass
    elif isinstance(response, mp.Reply):
        await message.channel.send(response.content, reference=message)
    elif isinstance(response, mp.Message):
        await message.channel.send(response.content)
    elif isinstance(response, mp.Reaction):
        await message.add_reaction(response.emoji)

    piety = await mp_instance.get_piety(message)
    if piety >= 0:
        print('updating...' + str(message.author.id))
        update_piety(message.author.id, piety)


def update_piety(uid: int, piety: int) -> None:
    piety_inc = 0
    if piety == 0:
        piety_inc = -500
    elif piety == 1:
        piety_inc = -100
    elif piety == 2:
        piety_inc = -50
    elif piety == 7:
        piety_inc = 50
    elif piety == 8:
        piety_inc = 100
    elif piety == 9:
        piety_inc = 500

    if piety_inc != 0:
        print('here')
        query = {'id': uid}
        post = {'piety': piety_inc}
        db_members.update_one(query, {'$inc': post})
        print('Modified piety by ' + str(piety_inc))


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel == None and after.channel != None:
        print(f'{member} joined voice!')    

        # Ping me when someone joins voice
        # Do not ping if I am already in voice
        for m in after.channel.members:
            if m.id == 307723444428996608: return
        await message_owner(f'{member} joined voice!')
    elif before.channel != None and after.channel == None:
        print(f'{member} left voice!')
#######################################


############# COMMANDS ################
@bot.tree.command(name='daily', description='Gambling! 100 is the winning score', guilds=guilds)
async def daily(ctx: discord.Interaction): 
    # Ensure everything has gone right
    if ctx.guild is None:
        print('/daily: guild is None!')
        return
    if not isinstance(ctx.channel, discord.channel.TextChannel):
        print('/daily: channel was not a text channel!')
        return
    
    m_id = ctx.user.id

    # 10% chance yogert kicks himself
    if m_id == 834559271277559819 and random() > 0.9:
        member = ctx.guild.get_member(834559271277559819)
        if member is not None:
            await member.kick(reason='You won the lottery!')

    # Get the last /daily timestamp from the database
    query = {'id': ctx.user.id}
    result = list(db_daily.find(query))
    last = None
    if len(result) == 0:
        last = str(dt.datetime.min)
    else:
        last = result[0]['last']
    last = dt.datetime.strptime(last, '%Y-%m-%d %H:%M:%S')
    now = dt.datetime.now().replace(microsecond=0)
    difference = now - last

    target_difference = 60 * 60 * 4     # 4 hours
    diff_seconds = 24 * 60 * 60 * difference.days + difference.seconds

    if diff_seconds < target_difference:
        pretty_future = target_difference - diff_seconds
        pretty_hours = int(pretty_future / (60 * 60))
        pretty_minutes = int(pretty_future / 60 % 60)
        pretty_seconds = int(pretty_future % 60)

        response = 'It has not been long enough since you last used /daily!\nPlease wait another '
        if pretty_hours == 1:
            response += f'{pretty_hours} hour '
        elif pretty_hours > 1:
            response += f'{pretty_hours} hours '

        if pretty_hours > 0 and pretty_minutes > 0 and pretty_seconds == 0:
            response += 'and '

        if pretty_minutes == 1:
            response += f'{pretty_minutes} minute '
        elif pretty_minutes > 1:
            response += f'{pretty_minutes} minutes '

        if pretty_minutes > 0 and pretty_seconds > 0:
            response += 'and '

        if pretty_seconds == 1:
            response += f'{pretty_seconds} second. '
        elif pretty_seconds > 1:
            response += f'{pretty_seconds} seconds. '
        await ctx.response.send_message(response, ephemeral=True)
        return

    # Update database
    post = {'id': m_id, 'last': str(now)}
    db_daily.update_one(query, {'$set': post}, upsert=True)

    val = randint(1, 100)
    print(f'Daily -> {ctx.user.name} got a {val}')
    if val == 100:
        if ctx.guild is None:
            print('none guild')
            return
        
        the_list = list(db_list.find({}))
        member_id = the_list[randint(0, len(the_list))]['id']

        member = await ctx.guild.fetch_member(member_id)
        name = member.nick
        if name == None:
            name = member.name

        await member.kick(reason='Someone else won the lottery!')

        await ctx.response.send_message('You rolled a perfect 100!', ephemeral=True)
        await ctx.channel.send(f'Congratulations, you win!\n{name} was kicked.')
    else:
        await ctx.response.send_message(f'You needed a 100. You rolled a {val}.', ephemeral=True)
        caller = ctx.guild.get_member(m_id)
        if caller is None:
            await ctx.channel.send('Someone had a skill issue.')
        else:
            caller_name = caller.nick
            if caller_name is None:
                caller_name = caller.name
            await ctx.channel.send(f'Skill issue <@{str(m_id)}>')
            

@bot.tree.command(name="list", description='This command is members-only!', guilds=guilds)
async def the_list(ctx: discord.Interaction, *, command: str):
    async def usage(tip: str) -> None:
        await ctx.response.send_message(tip, ephemeral=True)

    args = command.split(' ')
    if len(args) == 0:
        await usage('Usage: `/list [help|add] ...`')

    politburo_role = ctx.guild.get_role(1205643157732073512)
    party_role = ctx.guild.get_role(1205643117626392626)
    rabble_role = ctx.guild.get_role(1205643020502958080)

    subcommand = args[0]
    # Add target to the list
    if subcommand == 'add':
        user = ctx.user.id
        user = ctx.guild.get_member(user)
        if politburo_role not in user.roles and party_role not in user.roles:
            ctx.response.send_message('You are not allowed to use this command!\nAlerting the authorities...', ephemeral=True)
            politburo_channel = ctx.guild.get_channel(1206325612785045534)
            politburo_channel.send(f'{user.name} just tried doing /list ' + command + '!')
            print('/list add -> ' + command)
            return
        elif politburo_role not in user.roles:
            ctx.response.send_message('You are allowed to use this command, but you are not on the council.\nInforming the politburo...')
            politburo_channel = ctx.guild.get_channel(1206325612785045534)
            politburo_channel.send(f'{user.name} just tried doing /list ' + command + '!')
            print('/list add -> ' + command)
            return

        if len(args) != 2:
            await usage('Usage: `/list add [name]`\nExample: `/list add @Lion Bot`')
        uid = args[1][2:len(args[1]) - 1]

        # Add role to target
        member = ctx.guild.get_member(int(uid))
        if politburo_role in member.roles:
            await ctx.response.send_message(f'Hey <@{uid}>, <@{ctx.user.id}> just tried to add you to the list. Their fate is in your hands.')
            return
        list_role = ctx.guild.get_role(1216854346700951715)
        if list_role not in member.roles:
            await member.add_roles(list_role)
            ret += 2

        print(f'{ctx.user.name} just used /list add on {member.name}')

        ret = 0
        # Add target to database
        query = {'id': uid}
        result = list(db_list.find(query))
        if len(result) == 0:
            post = {'id': uid}
            db_list.insert_one(post)
            ret += 1

        if ret > 0:
            await ctx.response.send_message(f'<@{uid}> was added to the list!', ephemeral=True)
        else:
            await ctx.response.send_message(f'<@{uid}> is already on the list!', ephemeral=True)

    else:
        await usage('Usage: `/list [help|add] ...`')


@bot.tree.command(name='ck', description='I do a little roleplaying. Try /ck help', guilds=guilds)
async def ck(ctx: discord.Interaction, *, command: str):
    async def usage(tip: str) -> None:
        await ctx.response.send_message(tip, ephemeral=True)

    args = command.split(' ')
    if len(args) == 0:
        await usage('Usage: `/ck [help|enroll|stats]`')
        return
    
    subcommand = args[0]

    # Enroll user in Crusader Kings roleplay
    if subcommand == 'enroll':
        if len(args) != 2:
            await usage('Usage: `/ck enroll [NAME]`')
            return
        
        name = args[1]

        query = {'id': ctx.user.id}
        result = list(db_members.find(query))

        if len(result) == 0:
            # Create new member and add to database
            member = ms.Member(ctx.user.id, name)
            if connected_to_mongo:
                try:
                    db_members.insert_one(member.to_dict())
                    await ctx.response.send_message(f'You are now registered as **{member.rank.name} {member.name}**!')
                except pymongo.errors.OperationFailure:
                    logging.error("Something went wrong when trying to add member to database!")
        else:
            await ctx.response.send_message(f'You already enrolled!', ephemeral=True)
    # View stats of given player, self if no name provided
    elif subcommand == 'stats':
        name = ''
        if len(args) == 2:
            name = args[1]

        id = ctx.user.id if name == '' else int(name[2:len(name) - 1])

        query = {'id': id}
        result = list(db_members.find(query))

        if len(result) == 0 and name == '':
            await ctx.response.send_message('You have not enrolled with /ck yet!\nYou can do so using `/ck enroll [NAME]`', ephemeral=True)
        elif len(result) == 0:
            await ctx.response.send_message('That user has not enrolled with /ck yet!', ephemeral=True)
        else:
            member = ms.Member(result[0])
            await ctx.response.send_message(member.print_format())
    # Update user information
    elif subcommand == 'update':
        update_type = None if len(args) < 2 else args[1]
        new_field = ''
        for n in range(2, len(args)):
            if n != 2:
                new_field += ' '
            new_field += args[n]
        query = {'id': ctx.user.id}

        if update_type == 'name':
            if len(args) < 3:
                await usage('Usage: `/ck update name [NEW NAME]`')
                return
            
            post = {'id': ctx.user.id, 'name': new_field}
            db_members.update_one(query, {'$set': post})
            await ctx.response.send_message(f'Updated your name to {new_field}!')
        elif update_type == 'title':
            if len(args) < 3:
                await usage('Usage: `/ck update title [NEW TITLE]`')
                return
            
            post = {'id': ctx.user.id, 'title': new_field}
            db_members.update_one(query, {'$set': post})
            await ctx.response.send_message(f'Updated your title to {new_field}!')
        elif update_type == 'disposition':
            if len(args) < 3:
                await usage('Usage: `/ck update disposition [NEW DISPOSITION]`')
                return
            
            post = {'id': ctx.user.id, 'disposition': new_field}
            db_members.update_one(query, {'$set': post})
            await ctx.response.send_message(f'Updated your disposition to {new_field}!')
        else:
            await usage('Usage: `/ck update [name]`')
    # Print command usage
    else:
        await usage('Usage: `/ck [help|enroll|stats]`')


@bot.tree.command(name='debug', description='May only be used by the bot\'s owner', guilds=guilds)
async def debug(ctx: discord.Interaction, setting: str, arg0: str = ''):
    if ctx.user.id != 307723444428996608:
        await ctx.response.send_message('You are not permitted to use this command!', ephemeral=True)
        print(f'{ctx.user.name} just tried to use /debug')
        return

    if setting == 'add roles':
        if ctx.guild is None:
            print('add roles failed!')
            return
        
        role_name = arg0
        role = get(ctx.guild.roles, name=role_name)
        if role is None:
            print('couldnt find role!')
            return

        for member in ctx.guild.members:
            roles = member.roles
            has_role = False
            for irole in roles:
                if irole.name == role_name:
                    has_role = True
                    break

            if not has_role:
                await member.add_roles(role)
    elif setting == 'sync':
        print('[STATUS] Syncing commands...')
        if arg0 == '':
            await ctx.response.send_message('/debug sync requires another argument!\nUsage: /debug sync [global|local]', ephemeral=True)
            return
        elif arg0 == 'global':
            bot.tree.clear_commands(guild=None)
            # for guild in guilds:
                # await bot.tree.sync(guild=guild)
        elif arg0 == 'local':
            bot.tree.clear_commands(guild=ctx.guild)
            bot.tree.remove_command('ping')
            await bot.tree.sync(guild=ctx.guild)
        else:
            await ctx.response.send_message('Invalid argument for /debug sync!\nUsage: /debug sync [global|local]', ephemeral=True)
            return
        
        await ctx.response.send_message(f'Command tree synced!', ephemeral=True)
        print('[STATUS] Syncing complete!')
    elif setting == 'update database':
        m = ms.Member(-1, 'TEST')
        db_members.update_many({}, {'$set': {'gold': 0}})
        db_members.update_many({}, {'$set': {'gold_income': 1.0}})
        # db_members.update_many({'gold_income': {'$exists': False}}, {'$set': {'gold_income': m.gold_income}})
        # db_members.update_many({'prestige_income': {'$exists': False}}, {'$set': {'prestige_income': m.prestige_income}})
        # db_members.update_many({'piety_income': {'$exists': False}}, {'$set': {'piety_income': m.piety_income}})
        await ctx.response.send_message('Updated database successfully!', ephemeral=True)
    elif setting == 'test':
        print(list(db_list.find({})))
    else:
        await ctx.response.send_message(f'"{setting}" is an invalid subcommand!', ephemeral=True)


@bot.tree.command(name='ping', description='Checks the response time of the bot\'s server', guilds=guilds)
async def ping(ctx: discord.Interaction):
    await ctx.response.send_message(f'pong! *({int(bot.latency * 1000)}ms)*')


@bot.tree.command(name='disconnect', description='Disconnects the specified user from voice', guilds=guilds)
async def disconnect(ctx: discord.Interaction, member: discord.Member):
    # print(ctx.author)
    print(ctx.user.name + " used disconnect")

    if ctx.message != None:
        print('it worked')
        print(ctx.message)
        print(ctx.message.author)
        print(ctx.message.author.id)
    

    print(member.id)
    # brown id = 308437138855428117
    # lion id = 307723444428996608

    voice_state = member.voice

    if voice_state is None:
        return await ctx.response.send_message('Hey dumbass, the target has to be in voice to get disconnected.\nTry thinking a little bit before using random commands, okay?')

    await member.move_to(None)
    await ctx.response.send_message("done!", ephemeral=True)
#######################################


# Final initialization
file = open('./config/token', 'r')
token = file.read()
file.close()

bot.run(token, log_handler=handler, log_level=logging.INFO)
