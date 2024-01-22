import discord
import logging

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

file = open('./TOKEN', 'r')
token = file.read()
file.close()

# Logging
handler = logging.FileHandler(filename='./logs/lion_bot.log', encoding='utf-8', mode='w')

client.run(token, log_handler=handler, log_level=logging.INFO)
