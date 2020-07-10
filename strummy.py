import discord
from discord.ext import commands
from aux_forms import read_token

token = read_token(0)

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    bot.load_extension('cogs.music')
    bot.load_extension('cogs.genius')
    
bot.run(token)