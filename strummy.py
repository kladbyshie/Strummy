import discord
from discord.ext import commands

def read_token():
    with open("token.txt", "r") as tok:
        lines = tok.readlines()
        return(lines[0].strip())

token = read_token()

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    bot.load_extension('cogs.music')
    
bot.run(token)