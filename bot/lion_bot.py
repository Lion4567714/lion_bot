############### IMPORTS ###############
import discord
from discord.ext import commands
import logging

import pymongo
import pymongo.errors
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import sys
import urllib.parse

import message_processor as mp

from random import random
#######################################


# Discord Client
intents = discord.Intents.all()
intents.message_content = True
# discord_client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)
# tree = app_commands.CommandTree(discord_client)

# Logging
handler = logging.FileHandler(filename='./logs/lion_bot.log', encoding='utf-8', mode='w')

# Guilds
try:
    file = open('./config/guilds', 'r')
    guild_ids = file.read().splitlines()
    file.close()
except Exception as e:
    print("""
[ERROR]
Something went wrong when trying to read ./config/guilds!
Make sure the file exists and contains guilds ids separated by newlines.
    """)
    sys.exit()
guilds = []
for guild in guild_ids:
    guilds.append(discord.Object(id=guild))

# Bot stuff
mp_instance = mp.MessageProcessor()


############### MONGO #################
try:
    file = open('./config/mongo', 'r')
    mongo = file.read().splitlines()
    file.close()
except Exception as e:
    print("""
[ERROR]
Something went wrong when trying to read ./config/mongo!
Make sure the file exists and contains your mongo username and password.
          """)
    sys.exit()

mongo_user = urllib.parse.quote(mongo[0])
mongo_pass = urllib.parse.quote(mongo[1])

uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@discordcluster.ujcowjs.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

connected_to_mongo = False
try:
    mongo_client.admin.command('ping')
    connected_to_mongo = True
    print("Ping successful. Connected to MongoDB!")
except Exception as e:
    print("Ping unsuccessful. Continuing without MongoDB...")
    # print(e)

db = mongo_client.my_database
posts = db['posts']
#######################################


############### EVENTS ################
@bot.event
async def on_ready():
    for guild in guilds:
        await bot.tree.sync(guild=guild)
    print(f'Logged into discord as {bot.user}!')
    print("----- BEGIN LOG -----")


@bot.event
async def on_message(message: discord.Message):
    post = mp_instance.message_to_dict(message)

    if connected_to_mongo:
        try:
            posts.insert_one(post)
        except pymongo.errors.OperationFailure:
                logging.error("Something went wrong with sending a message to MongoDB!")

    if message.author == bot.user:
        return

    if random() > 0.98:
        if random() > 0.5:
            await message.channel.send('shut up')
        else:
            await message.channel.send('dumbass')

    response = mp_instance.process_message(message, 1)
    match response:
        case mp.Silent:
            pass
        case mp.Reply():
            await message.channel.send(response.content, reference=message)
        case mp.Message():
            await message.channel.send(response.content)
        case mp.Reaction():
            await message.add_reaction(response.emoji)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel == None and after.channel != None:
        print(f'{member} joined voice!')
        user = await bot.fetch_user(307723444428996608)
        await user.send(f'{member} joined voice!')
    elif before.channel != None and after.channel == None:
        print(f'{member} left voice!')
#######################################


############# COMMANDS ################
# @bot.command(guild=discord.Object['id'=976251686270144522])
# async def sync(ctx):
#     if ctx.author.id == 307723444428996608:
#         await bot.tree.sync()
            

@bot.tree.command(guilds=guilds)
async def test1(ctx):
    print(ctx)
    test: commands.Context = ctx
    print(test)
    print(test.author)
    await ctx.send("FUUUUUUCK")


@bot.tree.command(name='ping', guilds=guilds)
async def ping(ctx):
    await ctx.response.send_message('pong')


@bot.tree.command(name='test', guilds=guilds)
async def test(ctx):
    print(ctx)
    print(ctx.message)
    await ctx.response.send_message('Go fuck yourself', ephemeral=True)


@bot.tree.command(name='disconnect', guilds=guilds)
async def disconnect(ctx: discord.Interaction, member: discord.Member):
    # print(ctx.author)
    print(ctx.message)

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
