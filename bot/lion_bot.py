############### IMPORTS ###############
import discord
from discord.ext import commands
from discord import app_commands
import logging
from jinja2 import pass_context

import pymongo
import pymongo.errors
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import sys
import urllib.parse

import message_processor as mp

from random import random

import time
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
file = open('./config/guilds', 'r')
guild_ids = file.read().splitlines()
file.close()
guilds = []
for guild in guild_ids:
    guilds.append(discord.Object(id=guild))

# Bot stuff
mp_instance = mp.MessageProcessor()


############### MONGO #################
file = open('./config/mongo', 'r')
mongo = file.read().splitlines()
file.close()

mongo_user = urllib.parse.quote(mongo[0])
mongo_pass = urllib.parse.quote(mongo[1])

uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@discordcluster.ujcowjs.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

try:
    mongo_client.admin.command('ping')
    print("Ping successful. Connected to MongoDB!")
except Exception as e:
    print("Ping unsuccessful. Connected to MongoDB failed!")
    print(e)

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

    try:
        posts.insert_one(post)
    except pymongo.errors.OperationFailure:
        logging.error("Something went wrong with sending a message to MongoDB!")
        sys.exit(1)

    if message.author == bot.user:
        return

    if random() > 0.98:
        await message.channel.send("dumbass")

    response = mp_instance.process_message(message, 1)
    match response:
        case mp.Silent:
            pass
        case mp.Message():
            await message.channel.send(response.content)
        case mp.Reaction():
            await message.add_reaction(response.emoji)
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
