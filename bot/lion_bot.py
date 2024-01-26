import discord
from discord.ext import commands
import logging
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import message_processor as mp
import sys

DEBUG = False

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Logging
handler = logging.FileHandler(filename='./logs/lion_bot.log', encoding='utf-8', mode='w')

# MongoDB
file = open('./config/mongo', 'r')
mongo = file.read().splitlines()
file.close()
uri = f"mongodb+srv://{mongo[0]}:{mongo[1]}@discordcluster.ujcowjs.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(uri, server_api=ServerApi('1'))
db = mongo_client.my_database

try:
    mongo_client.admin.command('ping')
    print("Ping successful. Connected to MongoDB!")
except Exception as e:
    print(e)

posts = db['posts']
# End MongoDB

@bot.event
async def on_ready():
    guilds = discord.Object(id=[976251686270144522, 307725570429550592])
    bot.tree.copy_global_to(guild=guilds)
    await bot.tree.sync(guild=guilds) 
    
    print(f'Logged into discord as {bot.user}!')
    print('Begining chat log...')
    print('----- LOG -----')

@bot.event
async def on_message(message):
    post = mp.message_to_dict(message)
    mp.print_message(post, DEBUG)
    try:
        post_id = posts.insert_one(post)
    except pymongo.errors.OperationFailure:
        logging.error("Something went wrong with sending a message to MongoDB!")
        sys.exit(1)

    if message.author == bot.user:
        return

    response = mp.get_response(message.content)
    if len(response) != 0:
        await message.channel.send(response)

@bot.tree.command(name='ping')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('pong')  

@bot.tree.command(name='repeat')
async def repeat(interaction: discord.Interaction, message: str):
    await interaction.channel.send(message)

file = open('./config/token', 'r')
token = file.read()
file.close()

bot.run(token, log_handler=handler, log_level=logging.INFO)
