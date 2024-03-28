# TODO: Track who uses /daily and how often
# TODO: Increase odds of /daily working based on social credit
# TODO: Republican bot sentiments


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
import os
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
intents = discord.Intents.all()
# intents.members = True
# intents.message_content = True
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
db_config = db['config']
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

    response = await mp_instance.process_message(message, 1)
    if isinstance(response, mp.Silent):
        pass
    elif isinstance(response, mp.Reply):
        await message.channel.send(response.content, reference=message)
    elif isinstance(response, mp.Message):
        await message.channel.send(response.content)
    elif isinstance(response, mp.Reaction):
        await message.add_reaction(response.emoji)
        
    piety = response.piety
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


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # Make sure the bot isn't reacting to it's own reactions
    if bot.user == None:
        print('[WARNING] on_raw_reaction_add(): bot is not logged in!')
        return
    elif payload.user_id == bot.user.id:
        return
    
    # Make sure there are no None fields that will mess with anything
    if payload.guild_id == None:
        print('[ERROR] on_raw_reaction_add(): guild_id is missing!')
        return
    guild = bot.get_guild(payload.guild_id)
    if guild == None:
        print('[ERROR] on_raw_reaction_add(): guild could not be found!')
        return
    member = guild.get_member(payload.user_id)
    if member == None:
        print('[ERROR] on_raw_reaction_add(): member could not be found!')
        return

    # Get config message information
    query = {'id': payload.message_id}
    post = db_config.find_one(query)
    if post == None:
        return
    
    # Get the role from the database post
    emoji = '<:' + payload.emoji._as_reaction() + '>'
    role_id = int(post['map'][emoji][3:-1])
    role = guild.get_role(role_id)
    if role == None:
        print('[ERROR] on_raw_reaction_add(): role could not be found!')
        return
    
    await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    # Make sure the bot isn't reacting to it's own reactions
    if bot.user == None:
        print('[WARNING] on_raw_reaction_add(): bot is not logged in!')
        return
    elif payload.user_id == bot.user.id:
        return
    
    # Make sure there are no None fields that will mess with anything
    if payload.guild_id == None:
        print('[ERROR] on_raw_reaction_add(): guild_id is missing!')
        return
    guild = bot.get_guild(payload.guild_id)
    if guild == None:
        print('[ERROR] on_raw_reaction_add(): guild could not be found!')
        return
    member = guild.get_member(payload.user_id)
    if member == None:
        print('[ERROR] on_raw_reaction_add(): member could not be found!')
        return

    # Get config message information
    query = {'id': payload.message_id}
    post = db_config.find_one(query)
    if post == None:
        return
    
    # Get the role from the database post
    emoji = '<:' + payload.emoji._as_reaction() + '>'
    role_id = int(post['map'][emoji][3:-1])
    role = guild.get_role(role_id)
    if role == None:
        print('[ERROR] on_raw_reaction_add(): role could not be found!')
        return
    
    await member.remove_roles(role)
#######################################


############# COMMANDS ################
@bot.tree.command(name='help', description='Use /help to find out how to use Lion Bot!', guilds=guilds)
async def help(ctx: discord.Interaction):
    output = \
"""
Available commands:
`/help`: Information on how to use Lion Bot and his commands.
`/ck [help|enroll|stats|update]`: Crusader Kings-style roleplay. Join in!
\t `help`: Usage information for /ck.
\t `enroll [name]`: Enroll yourself in the ck rolepray under `name`.
\t `stats [name]`: Check the stats for any user. Leave `name` blank to see yourself.
\t `update [name|disposition|title] [new]`: Update your own information.  
`/daily`: Roll a d100 for a chance to win a real treat! Available every 4 hours.
`/disconnect [target]`: Disconnect a user (the target) from voice chat. (Scandalous!)
`/ping`: Test the availability and latency of Lion Bot.

Restricted commands:
`/debug`: Only available for <@307723444428996608>.
`/list [help|add]`: All things related to *the list*. Only available for party members and above.
\t `help`: Usage information for /list.
\t `add [target]`: Add someone (the target) to *the list*.

The only rule is that <@1199041303221121025> is the Pope. Praise and revere him, for it is He who decides your fate.
"""
    await ctx.response.send_message(output, ephemeral=True)


@bot.tree.command(name='daily', description='Gambling! 95+ is the winning score', guilds=guilds)
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
    db_members.update_one(query, {'$inc': {'prestige': 50}})

    val = randint(1, 100)
    print(f'Daily -> {ctx.user.name} got a {val}')
    if val >= 95:
        if ctx.guild is None:
            print('none guild')
            return
        
        the_list = list(db_list.find({}))
        member_id = the_list[randint(0, len(the_list))]['id']

        member = await ctx.guild.fetch_member(member_id)
        name = member.nick
        if name == None:
            name = member.name

        await member.kick(reason='You were excommunicated by our Lord and Saviour, Lion Bot. We hope you enjoyed your stay.')
        db_list.delete_one({'id': str(member.id)})

        await ctx.response.send_message(f'You rolled a perfect {val}!', ephemeral=True)
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
            await ctx.response.send_message('You are not allowed to use this command!\nAlerting the authorities...', ephemeral=True)
            politburo_channel = ctx.guild.get_channel(1206325612785045534)
            politburo_channel.send(f'{user.name} just tried doing /list ' + command + '!')
            print('/list add -> ' + command)
            return
        elif politburo_role not in user.roles:
            await ctx.response.send_message('You are allowed to use this command, but you are not on the council.\nInforming the politburo...')
            politburo_channel = ctx.guild.get_channel(1206325612785045534)
            politburo_channel.send(f'{user.name} just tried doing /list ' + command + '!')
            print('/list add -> ' + command)
            return

        if len(args) != 2:
            await usage('Usage: `/list add [name]`\nExample: `/list add @Lion Bot`')
            return
    
        uid = args[1][2:len(args[1]) - 1]
        ret = 0

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
        await usage('Usage: `/ck [help|enroll|stats|update]`')
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
            await usage('Usage: `/ck update [name|title|disposition] [NEW]`')
    # Print command usage
    else:
        await usage('Usage: `/ck [help|enroll|stats|update]`')


@bot.tree.command(name='debug', description='May only be used by the bot\'s owner', guilds=guilds)
async def debug(ctx: discord.Interaction, *, command: str):
    async def usage(usage_info: str) -> None:
        await ctx.response.send_message('Usage: `' + usage_info + '`', ephemeral=True)

    # Only the bot owner is allowed to use this command
    if ctx.user.id != 307723444428996608:
        await ctx.response.send_message('You are not permitted to use this command!', ephemeral=True)
        print(f'{ctx.user.name} just tried to use /debug')
        return

    args = command.split(' ')
    print(args)
    if args[0] == 'config_message':
        # "Config messages" are messages you react to that serve some purpose, like granting roles
        # The terminology is completely made up. I have no idea what they're actually called lol
        # if args[1] == 'add':
            args[1] = command.split('"')[1]
            args = args[:2] + command.split('"')[2].split(' ')[1:]  # Combine the message in quotes into one argument
            if len(args) < 4 or len(args) % 2 == 1:    # Expecting one role for every reaction and at least one pair of those
                await usage('/debug config_message "message" ([REACTION] [ROLE])+')
                return

            print(args)

            message = args[1] + '\n'
            for i in range(2, len(args), 2):
                message += args[i] + ' -> ' + args[i + 1] + '\n'

            await ctx.response.send_message('Creating config message...', ephemeral=True)
            bot_message = await ctx.channel.send(message)
            for i in range(2, len(args), 2):
                await bot_message.add_reaction(args[i])

            post = {'id': bot_message.id}
            reaction_to_role = {}
            for i in range(2, len(args), 2):
                reaction_to_role[args[i]] = args[i + 1]
            post['map'] = reaction_to_role
            db_config.insert_one(post)
            print('Added config message to db_config!')
        # elif args[1] == 'remove':
            # print('Removed config message from db_config!')
    else:
        await usage('/debug config_message')

    # if subcommand == 'add roles':
    #     if ctx.guild is None:
    #         print('add roles failed!')
    #         return
        
    #     role_name = arg0
    #     role = get(ctx.guild.roles, name=role_name)
    #     if role is None:
    #         print('couldnt find role!')
    #         return

    #     for member in ctx.guild.members:
    #         roles = member.roles
    #         has_role = False
    #         for irole in roles:
    #             if irole.name == role_name:
    #                 has_role = True
    #                 break

    #         if not has_role:
    #             await member.add_roles(role)
    # elif subcommand == 'sync':
    #     print('[STATUS] Syncing commands...')
    #     if arg0 == '':
    #         await ctx.response.send_message('/debug sync requires another argument!\nUsage: /debug sync [global|local]', ephemeral=True)
    #         return
    #     elif arg0 == 'global':
    #         bot.tree.clear_commands(guild=None)
    #         # for guild in guilds:
    #             # await bot.tree.sync(guild=guild)
    #     elif arg0 == 'local':
    #         bot.tree.clear_commands(guild=ctx.guild)
    #         bot.tree.remove_command('ping')
    #         await bot.tree.sync(guild=ctx.guild)
    #     else:
    #         await ctx.response.send_message('Invalid argument for /debug sync!\nUsage: /debug sync [global|local]', ephemeral=True)
    #         return
        
    #     await ctx.response.send_message(f'Command tree synced!', ephemeral=True)
    #     print('[STATUS] Syncing complete!')
    # elif subcommand == 'update database':
    #     m = ms.Member(-1, 'TEST')
    #     db_members.update_many({}, {'$set': {'gold': 0}})
    #     db_members.update_many({}, {'$set': {'gold_income': 1.0}})
    #     # db_members.update_many({'gold_income': {'$exists': False}}, {'$set': {'gold_income': m.gold_income}})
    #     # db_members.update_many({'prestige_income': {'$exists': False}}, {'$set': {'prestige_income': m.prestige_income}})
    #     # db_members.update_many({'piety_income': {'$exists': False}}, {'$set': {'piety_income': m.piety_income}})
    #     await ctx.response.send_message('Updated database successfully!', ephemeral=True)
    # elif subcommand == 'free daily':
    #     new_last = dt.datetime.now().replace(microsecond=0)
    #     new_last = new_last.replace(day=new_last.day - 1)
    #     db_daily.update_many({}, {'$set': {'last': str(new_last)}})
    #     await ctx.response.send_message('Awarded a free /daily to everyone!')
    # elif subcommand == 'test':
    #     if ctx.guild == None:
    #         return
        
    #     guild_members = [int(member.id) for member in list(ctx.guild.members)]
    #     list_members = [int(doc['id']) for doc in list(db_list.find({}))]

    #     for list_member in list_members:
    #         if list_member not in guild_members:
    #             print(list_member, 'bruh')
    #             db_list.delete_one({'id': str(list_member)})
    # else:
    #     await ctx.response.send_message(f'"{setting}" is an invalid subcommand!', ephemeral=True)


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
