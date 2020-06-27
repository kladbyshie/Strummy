import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    bot.load_extension('cogs.music')
    
bot.run('NzIyOTE0MDI4MjQyMDc1NzQ5.Xvevlw.PHM4McpQaKXVnKCHZ8erI5O5VgU')