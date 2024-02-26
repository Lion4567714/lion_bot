# TODO: Track who uses /daily and how often
# TODO: Increase odds of /daily working based on social credit
# TODO: Republican bot sentiments
# TODO: New pious pfp


############### IMPORTS ###############
import discord
from discord.ext import commands
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
import pytz
#######################################


############## WORK ZONE ##############
ck_members = {}
#######################################


def print_error(path: str, e: Exception, is_fatal: bool = False) -> None:
    print(f'[ERROR] Something went wrong when trying to read {path}!')
    print(e)
    if is_fatal: sys.exit()


# Load logs
mp_instance = mp.MessageProcessor()
daily_log_temp = {}
daily_log: dict[int, dt.datetime] = {}
try:
    # Activity log
    path = './bot/messaging/activity'
    file = open(path, 'r')
    mp_instance.activity = ast.literal_eval(file.read())
    file.close()

    # Daily log
    path = './logs/daily.log'
    file = open(path, 'r')
    daily_log_temp = ast.literal_eval(file.read())
    file.close()
except Exception as e:
    print_error(path, e, True)

# Change strings to datetimes
for key in daily_log_temp.keys():
    daily_log[key] = dt.datetime.strptime(daily_log_temp[key], '%Y-%m-%d %H:%M:%S.%f')


############## SIGNALS ################
def signal_handler(sig, frame):
    try:
        # Log activity
        path = './bot/messaging/activity'
        file = open(path, 'w')
        file.write(str(mp_instance.activity))
        file.close()

        # Log daily
        path = './logs/daily.log'
        file = open(path, 'w')
        daily_log_out = {}
        for key in daily_log.keys():
            daily_log_out[key] = str(daily_log[key])
        file.write(str(daily_log_out))
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
posts = db['posts']
db_members = db['members']
#######################################


############### EVENTS ################
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


@bot.event
async def on_message(message: discord.Message):
    post = mp_instance.message_to_dict(message)
    mp_instance.log_activity(post)

    if connected_to_mongo:
        try:
            posts.insert_one(post)
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


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel == None and after.channel != None:
        print(f'{member} joined voice!')    

        # Ping me when someone joins voice
        # Do not ping if I am already in voice
        for m in after.channel.members:
            if m.id == 307723444428996608: return
        user = await bot.fetch_user(307723444428996608)
        await user.send(f'{member} joined voice!')
    elif before.channel != None and after.channel == None:
        print(f'{member} left voice!')
#######################################


############# COMMANDS ################
@bot.tree.command(name='daily', description='Gambling! 100 is the winning score', guilds=guilds)
async def daily(ctx: discord.Interaction): 
    m_id = ctx.user.id

    if ctx.guild is None:
        print('/daily: guild is None!')
        return

    # 10% chance yogert kicks himself
    if m_id == 834559271277559819 and random() > 0.9:
        member = ctx.guild.get_member(834559271277559819)
        if member is not None:
            await member.kick(reason='You won the lottery!')

    if m_id not in daily_log:
        daily_log[m_id] = dt.datetime.min
    difference = dt.datetime.now() - daily_log[m_id]

    target_difference = 60 * 60 * 4     # 4 hours

    diff_seconds = 24 * 60 * 60 * difference.days + difference.seconds
    pretty_future = target_difference - diff_seconds
    pretty_hours = int(pretty_future / (60 * 60))
    pretty_minutes = int(pretty_future / 60 % 60)
    pretty_seconds = int(pretty_future % 60)

    if diff_seconds > target_difference:
        cooldown_over = True
        print('/daily it has been long enough!')
    else:
        await ctx.response.send_message(f'It has not been long enough since you last used /daily!\nPlease wait another {pretty_hours} hours {pretty_minutes} minutes and {pretty_seconds} seconds.', ephemeral=True)
        print('/daily it has NOT been long enough!')


    if cooldown_over:
        daily_log[m_id] = dt.datetime.now()
    else:
        return

    if not isinstance(ctx.channel, discord.channel.TextChannel):
        print('botkick: channel was not a text channel!')
        return
    
    val = randint(1, 100)

    if val == 100:
        if ctx.guild is None:
            print('none guild')
            return
        
        the_list = [
                    171062001303420928, # ardo
                    171062001303420928, # ardo
                    731008459041931396, # arsenal
                    308437138855428117, # brown
                    370079779917004800, # jerry
                    138133846301474816, # nyanusmaps
                    143210335594086400, # pacmen
                    143210335594086400, # pacmen
                    879882591929532437, # starry
                    834559271277559819, # yogert
                    ]
        member_id = the_list[randint(0, len(the_list))]

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
            await ctx.channel.send('Skill issue <@' + str(m_id) + '>')
            

@bot.tree.command(name='ck', description='I do a little roleplaying', guilds=guilds)
async def ck(ctx: discord.Interaction, subcommand: str = '', name: str = ''):
    # Enroll user in Crusader Kings roleplay
    if subcommand == 'enroll':
        if name == '':
            await ctx.response.send_message('Usage: `/ck enroll [NAME]`', ephemeral=True)
        else:
            query = {'id': ctx.user.id}
            result = list(db_members.find(query))

            if len(result) == 0:
                # Create new member and add to database
                member = ms.Member(ctx.user.id, name)
                ck_members[ctx.user.id] = member
                if connected_to_mongo:
                    try:
                        db_members.insert_one(member.to_dict())
                    except pymongo.errors.OperationFailure:
                        logging.error("Something went wrong when trying to add member to database!")
            else:
                await ctx.response.send_message(f'You already enrolled!', ephemeral=True)
            if member != None:
                await ctx.response.send_message(f'You are now registered as **{member.rank.name} {member.name}**!')
    # View stats of given player, self if no name provided
    elif subcommand == 'stats':
        id = ctx.user.id if name == '' else name[2:len(name) - 1]

        query = {'id': id}
        result = list(db_members.find(query))

        if len(result) == 0 and name == '':
            await ctx.response.send_message('You have not enrolled with /ck yet!\nYou can do so using `/ck enroll [NAME]`', ephemeral=True)
        elif len(result) == None:
            await ctx.response.send_message('That user has not enrolled with /ck yet!', ephemeral=True)
        else:
            member = ms.Member(result[0])
            await ctx.response.send_message(member.print_format())
    # Print command usage
    else:
        await ctx.response.send_message('Usage: `/ck [enroll|stats]`', ephemeral=True)


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
    elif setting == 'test':
        # bot.tree.remove_command("ping", guild=None)
        # for guild in guilds:  
            # await bot.tree.sync(guild=guild)
        print(await bot.tree.fetch_commands())
        # print(bot.tree.client.remove_command("ping"))
        print(bot.tree.get_commands(guild=guilds[0]))
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        test = bot.tree.remove_command(arg0)
        print('test: ' + str(test))
        await ctx.response.send_message("tested")
    else:
        await ctx.response.send_message(f'"{setting}" is an invalid subcommand!', ephemeral=True)


# @bot.tree.command(name='test1', guilds=guilds)
# async def test1(ctx: discord.Interaction):
#     if isinstance(ctx.user, discord.User):
#         print('[ERROR] Found discord.User type where discord.Member type was needed!')
#         return

#     member: discord.Member = ctx.user

#     role = get(member.guild.roles, name='[TEST]')
#     if not isinstance(role, discord.Role):
#         print('[ERROR] Role not found!')
#         return

#     await member.add_roles(role)


@bot.tree.command(name='ping', description='Checks the response time of the bot\'s server', guilds=guilds)
async def ping(ctx: discord.Interaction):
    await ctx.response.send_message(f'pong! *({int(bot.latency * 1000)}ms)*')


# @bot.tree.command(name='test', guilds=guilds)
# async def test(ctx):
#     await ctx.response.send_message('https://tenor.com/view/shrek-stop-talking-five-minutes-be-yourself-please-gif-13730564', ephemeral=True)


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


# @tree.command(name='timer', guilds=guilds)
# async def timer(interaction: discord.Interaction, delay: int):
#     time.sleep(delay)
#     await interaction.response.send_message("Timer's up!")


# @tree.command(name='debug', guilds=guilds)
# async def debug(interaction: discord.Interaction, setting: str):
#     match setting:
#         case 'clear commands':
#             tree.clear_commands(guild=interaction.guild)
#             await interaction.response.send_message('Cleared commands!')
#         case _:
#             await interaction.response.send_message(f'"{setting}" is an invalid setting!')
#######################################


# Final initialization
file = open('./config/token', 'r')
token = file.read()
file.close()

bot.run(token, log_handler=handler, log_level=logging.INFO)
