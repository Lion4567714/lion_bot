############### IMPORTS ###############
import discord
from discord import app_commands
import logging

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import sys
import urllib
import message_processor as mp
#######################################


# Discord Client
intents = discord.Intents.all()
intents.message_content = True
discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)

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
    # logging.info()
    print("Ping successful. Connected to MongoDB!")
except Exception as e:
    print("Ping unsuccessful. Connected to MongoDB failed!")
    print(e)

db = mongo_client.my_database
posts = db['posts']
#######################################


async def read_terminal():
    print("im running")
    while(True):
        text = input()
        print(text)


# Final initialization
file = open('./config/token', 'r')
token = file.read()
file.close()

discord_client.run(token, log_handler=handler, log_level=logging.INFO)


############### EVENTS ################
@discord_client.event
async def on_ready():
    for guild in guilds:
        await tree.sync(guild=guild)
    print(f'Logged into discord as {discord_client.user}!')
    print("----- BEGIN LOG -----")


@discord_client.event
async def on_message(message: discord.Message):
    post = mp_instance.message_to_dict(message)

    try:
        post_id = posts.insert_one(post)
    except pymongo.errors.OperationFailure:
        logging.error("Something went wrong with sending a message to MongoDB!")
        sys.exit(1)

    if message.author == discord_client.user:
        return

    response = mp_instance.process_message(message, 1)
    if type(response) == mp.Message:
        if len(response.content) != 0:
            await message.channel.send(response.content)
    elif type(response) == mp.Reaction:
        await message.add_reaction(response.emoji)
#######################################


############# COMMANDS ################
@tree.command(name='ping', guilds=guilds)
async def ping(interaction):
    await interaction.response.send_message('pong')


@tree.command(name='test', guilds=guilds)
async def test(interaction):
    await interaction.response.send_message('Go fuck yourself')


@tree.command(name='disconnect', guilds=guilds)
async def disconnect(interaction: discord.Interaction, member: discord.Member):
    voice_state = member.voice

    if voice_state is None:
        return await interaction.response.send_message('Hey dumbass, the target has to be in voice to get disconnected.\nTry thinking a little bit before using random commands, okay?')

    await member.move_to(None)


@tree.command(name='debug', guilds=guilds)
async def debug(interaction: discord.Interaction, setting: str):
    match setting:
        case 'clear commands':
            tree.clear_commands(guild=interaction.guild)
            await interaction.response.send_message('Cleared commands!')
        case _:
            await interaction.response.send_message(f'"{setting}" is an invalid setting!')
#######################################