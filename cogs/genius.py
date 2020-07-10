import asyncio
import discord
import requests
import bs4
import re
from discord.ext import commands
from discord import Embed
from itertools import chain
from aux_forms import argsmachine, read_token
import math

token = read_token(1)

class Song():
    def __init__(self, title, url, wholeitem):
        self.title = title
        self.url = url
        self.wholeitem = wholeitem
        self.lyrics = None

class Genius(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.songqueue = []
        self.states = {}

    @commands.command()
    async def genius(self, ctx, *args):
        """Searches Genius for song lyrics to pull all lyrics into the chat"""
        args = argsmachine(args)
        async with ctx.channel.typing():
            if len(args) > 0:
                headers = {'Authorization': 'Bearer ' + token}
                search_url = f'https://api.genius.com/search?q={args}'
                response = requests.get(search_url, headers=headers)
                response = response.json()
                allitems = []
                for item in response['response']['hits']:
                    new = item['result']
                    newsong = Song(new['full_title'], new['url'], new)
                    allitems.append(newsong)
                titlelist = []
                counter = 1
                for item in allitems:
                    newline = f'{counter}. {item.title}'
                    titlelist.append(newline)
                    counter += 1
                string = '\n'
                embed = Embed()
                embed.description = string.join(titlelist)
                await ctx.channel.send('Here are some results of the songs that you wanted. Type in the # of which result you want the lyrics to, or "no" to back out!', embed=embed)

                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                while True:
                    try:
                        message = await self.bot.wait_for('message', check = check, timeout=30)
                        message = message.content.strip()
                        if message == 'no':
                            break
                        else:
                            message = int(message)-1
                            break
                    except asyncio.TimeoutError:
                        await ctx.send("You didn't reply in time! Enter the #.")
                        continue
                    except:
                        await ctx.send(f"Try entering the # again, or enter 'no' to exit the search command.")
                        continue

                try:
                    chosensong = allitems[message]
                    site = requests.get(chosensong.url)
                    site = bs4.BeautifulSoup(site.text, features='html.parser')
                    chosensong.lyrics = site.find("div", class_="lyrics").get_text()
                    
                    #Discord supports only 2048 characters in each embed message so this is used to break it up into multiple messages
                    messages_needed = math.ceil(len(chosensong.lyrics) / 2048)
                    lyricsembed=Embed()
                    counter = 1
                    currentchar = 0
                    nextchar = 2048
                    while messages_needed >= counter:
                        lyrics = chosensong.lyrics[currentchar:nextchar]
                        lyricsembed.description = lyrics
                        await ctx.send(f'Here are the lyrics for `{chosensong.title}`, `{counter}`/`{messages_needed}`!', embed=lyricsembed)
                        currentchar += 2048
                        nextchar += 2048
                        counter += 1
                except:
                    await ctx.send(f"Stopping the genius command.")
            else:
                await ctx.send(f"Can't really search for lyrics if there are none provided, right? Try again with words, song titles, or artist names.")

def setup(bot):
    bot.add_cog(Genius(bot))