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
# TODO: Move guilds to a file and read them in
guilds = [discord.Object(id=976251686270144522), discord.Object(id=307725570429550592)]

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


@discord_client.event
async def on_ready():
    for guild in guilds:
        await tree.sync(guild=guild)
    print(f'Logged into discord as {discord_client.user}!')

@discord_client.event
async def on_message(message):
    post = mp.message_to_dict(message)
    print(post)
    try:
        post_id = posts.insert_one(post)
    except pymongo.errors.OperationFailure:
        logging.error("Something went wrong with sending a message to MongoDB!")
        sys.exit(1)

    if message.author == discord_client.user:
        return

    response = mp.get_response(message.content)
    if len(response) != 0:
        await message.channel.send(response)
        

############# COMMANDS ################
@tree.command(name='ping', guilds=guilds)
async def ping(interaction):
    await interaction.response.send_message('pong')

@tree.command(name='test', guilds=guilds)
async def test(interaction):
    await interaction.response.send_message('Go fuck yourself')

# @tree.command(name='disconnect', guilds=guilds)
# async def disconnect(interaction: discord.Interaction, member: discord.Member):
#     voice_state = member.voice

#     if voice_state is None:
#         # Exiting if the user is not in a voice channel
#         return await interaction.response.send_message('Hey dumbass, you have to be in voice to get disconnected.\nTry thinking a little bit before using random commands, okay?')
#     else:
#         await member.move_to(None)

#######################################


# Final initialization
file = open('./config/token', 'r')
token = file.read()
file.close()

discord_client.run(token, log_handler=handler, log_level=logging.INFO)
