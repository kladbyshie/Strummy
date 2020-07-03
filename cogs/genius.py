import asyncio
import discord
import requests
import bs4
from discord.ext import commands
from discord import Embed

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
        newargs = []
        for item in args:
            item.strip()
            newargs.append(item)
        query = '%20'.join(newargs)
        if len(query) > 0:
            headers = {'Authorization': 'Bearer ' + 'To_00Vy-whV08bXPjqKEQrVxHm3b4ThuMSvG-_tPi58DR22oJa4crHKpRjzFE2vi'}
            search_url = f'https://api.genius.com/search?q={query}'
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
                    if message.content.strip() == 'no':
                        break
                    else:
                        numeral = message.content.strip()
                        message2 = int(numeral)-1
                        message2 = int(message2)
                        break
                except asyncio.TimeoutError:
                    await ctx.send("You didn't reply in time! Enter the #.")
                    continue
                except:
                    await ctx.send(f"I read that as `{message.content.strip()}`, which isn't an option. Try entering the # again, or enter 'no' to exit the search command.")
                    continue

            try:
                songitem = allitems[message2]
                site = requests.get(songitem.url)
                site = bs4.BeautifulSoup(site.text, features='html.parser')
                lyrics = site.find("div", class_="lyrics").get_text()
                lyricsembed=Embed()
                lyricsembed.description = lyrics
                await ctx.channel.send(f'Here are the lyrics for `{songitem.title}`!', embed=lyricsembed)
            except:
                await ctx.send("Stopping the genius command.")
        else:
            await ctx.send(f"Can't really search for lyrics if there are none provided, right? Try again with words, song titles, or artist names.")

def setup(bot):
    bot.add_cog(Genius(bot))