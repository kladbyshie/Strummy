import asyncio
import discord
import youtube_dl
import requests
import bs4
import re
import pandas as pd
import os
from discord.ext import commands
from discord import Embed
from itertools import chain
from aux_forms import argsmachine

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'audio-quality': 9,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class Song():
    """Class used in assigning songs to queue"""
    def __init__(self, title, url, player):
        self.title = title
        self.url = url
        self.player = player

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options, executable = "C:/ffmpeg/bin/ffmpeg.exe"), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.songqueue = []
        self.states = {}
        self.loopstatus = False
        self.loopplayer = None

    @staticmethod
    async def add(self, ctx, url):
        """Helper function for converting added songs to players and adding them to the songqueue"""
        async with ctx.channel.typing():
            player = await YTDLSource.from_url(url)
            newsong = Song(player.title,player.url,player)
            self.songqueue.append(newsong)
            await ctx.send(f"Adding `{player.title}` to the queue!")

    @staticmethod
    async def voicechecker(self, ctx):
        """Helper function for checking if author is connected to a voice channel"""
        def voicecheck(ctx):
            return ctx.author.voice

        while True:
            if ctx.voice_client is None:
                if ctx.author.voice:
                    await ctx.author.voice.channel.connect()
                    break
                else:
                    await ctx.send("You need to join a voice channel first! I need to know where to go.")
                    try: 
                        await self.bot.wait_for('voice_state_update', check = voicecheck, timeout=30)
                        await ctx.author.voice.channel.connect()
                        break
                    except:
                        continue
            else:
                continue
 
    @staticmethod
    async def returnqueue(self, ctx):
        """Helper function to create a songqueue paragraph chunk, used for printing queue"""
        if len(self.songqueue) == 0:
            return('No songs are in the queue.')
        else:
            queue2 = []
            counter = 1
            for item in self.songqueue:
                newline = f"{counter}. `{item.title}`"
                queue2.append(newline)
                counter += 1
            string = '\n'
            fulltext = string.join(queue2)
            return(fulltext)
    
    @commands.command(description = 'Plays the song URL or song name (from Youtube). If song is currently playing, adds it to the queue')
    async def play(self, ctx, *args):
        """Plays from a url or song title"""
        args = argsmachine(args)
        if args:
            await self.add(self, ctx, args)

        if not hasattr(ctx.voice_client, 'is_playing'):
            await self.voicechecker(self, ctx)
            song = self.songqueue.pop(0).player
            self.playsong(ctx,song)
            await ctx.send(f'Now playing: `{song.title}`')

    def playsong(self, ctx, song):
        client = ctx.guild.voice_client
        def aftersong(err):
            if self.loopstatus is True:            
                song = self.loopplayer
                self.playsong(ctx, song)
            else:
                if len(self.songqueue) > 0:
                    song2 = self.songqueue.pop(0).player
                    self.states['now_playing'] = song2.title
                    self.loopplayer = song2
                    self.playsong(ctx, song2)
                else:
                    asyncio.run_coroutine_threadsafe(client.disconnect(), self.bot.loop)
                    self.states['now_playing'] = 'Nothing. Nothing is currently playing.'

        client.pause()
        self.states['now_playing'] = song.title
        self.loopplayer = song
        client.play(song, after= aftersong)
    
    @commands.command(aliases = ['now'], description = 'Shows the name of the song currently playing')
    async def nowplaying(self, ctx):
        """Shows the name of current song playing"""

        await ctx.send(f"Now Playing: `{self.states['now_playing']}`")

    @commands.command()
    async def loop(self, ctx):

        if self.loopstatus is True:
            self.loopstatus = False
            await ctx.send('Turning the loop `off`!')
        else:
            self.loopstatus = True
            await ctx.send('Turning the loop `on`!')

    @commands.command(description = 'Shows the song queue, or plays the song in queue if you do !queue #')
    async def queue(self, ctx, selector=None):
        """Shows the song queue, or plays the song in queue if you do !queue #"""
        if selector:
            song = self.songqueue.pop(int(selector)-1).player
            self.playsong(ctx, song)
            await ctx.send(f'Playing `{song.title}`')
        else:
            queue = await self.returnqueue(self,ctx)
            embed=Embed()
            embed.description = queue
            await ctx.send(embed=embed)

    @commands.command(description = 'Searches YouTube and prints the top 10 results. Type in the # of the song you want added to the queue, or "no" to exit the command!')
    async def search(self, ctx, *args):
        """Searches youtube for song name and lets user select from 10 results"""
        async with ctx.channel.typing():                
            while True:
                try:
                    searchterm = argsmachine(args)
                    item = requests.get('https://www.youtube.com/results?search_query=' + searchterm)
                    soup = bs4.BeautifulSoup(item.text, features='html.parser')
                    allvids = soup.findAll('a',attrs={'class':'yt-uix-tile-link'})[:10]                   
                    new = pd.DataFrame()
                    counter = 1
                    for item in allvids:
                        newline = {}
                        newline['Title'] = item['title']
                        newline['Href'] = 'https://www.youtube.com' + item['href']
                        newline['Name'] = f"{counter}. {newline['Title']} - {newline['Href']}"
                        new = new.append(newline, ignore_index=True)
                        counter += 1
                    string = '\n'
                    embed = Embed()
                    embed.description = string.join(new)
                    await ctx.channel.send(embed=embed)
                    break
                except:
                    continue

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            while True:
                try:
                    message = await self.bot.wait_for('message', check = check, timeout=30)
                    if message.content == 'no':
                        break
                    else:
                        message = int(message.content)-1
                        break
                except asyncio.TimeoutError:
                    await ctx.send("You didn't reply in time! Enter the #.")
                    continue
                except:
                    await ctx.send("Are you SURE that was a number from 1 to 10? Try entering the # again, or enter 'no' to exit the search command.")
                    continue
            
            try:
                await self.add(self, ctx, new['Href'][message])
                if not hasattr(ctx.voice_client, 'is_playing'):
                    await self.voicechecker(self, ctx)
                    song = self.songqueue.pop(0).player
                    self.playsong(ctx,song)
                    await ctx.send(f'Now Playing: `{song.title}`')
            except:
                await ctx.send("Stopping the search command.")
    
    @commands.command(aliases = ['vol'], description = 'Shows the current volume, or changed the volume to the # specified (default is 50)')
    async def volume(self, ctx, volume: int = None):
        """Changes the player's volume"""
        client = ctx.guild.voice_client

        if client is None:
            return await ctx.send("Not connected to a voice channel.")

        if not volume:
            return await ctx.send(
                f":speaker: My current player volume is `{client.source.volume * 100}`%."
            )

        client.source.volume = volume / 100
        await ctx.send(f":speaker: Changed volume to `{volume}`%")

    @commands.command(description = 'Stops the music, disconnects the bot, and clears the song queue')
    async def stop(self, ctx):
        """Stops and disconnects the bot, and clears queue"""
        await ctx.voice_client.disconnect()

    @commands.command(aliases = ['s'], description = 'Skips the current song')
    async def skip(self, ctx):
        """Skips the current song and plays the next song"""
        player = ctx.guild.voice_client
        if len(self.songqueue) == 0 :
            await ctx.send("There are no songs in the queue! Just going to disconnect...")
            await ctx.voice_client.disconnect()
        else:
            if not hasattr(ctx.voice_client, 'is_playing'):
                song = self.songqueue.pop(0).player
                await ctx.send(f'Skipping current song`! Next song is going to be `{song.title}`')
            else:
                player.pause()
                song = self.songqueue.pop(0).player
                await ctx.send(f'Skipping current song! Now playing: `{song.title}`')
                self.playsong(ctx,song)

    @commands.command(aliases = ['resume'], description = 'Pauses or resumes the song playing. The two are interchangeable (ie. !pause will resume as well and vice versa)')
    async def pause(self, ctx):
        """Pauses or resumes the current song"""

        player = ctx.guild.voice_client
        if player.is_paused():
            player.resume()
            await ctx.send(":play_pause: Resumed.")
        else:
            player.pause()
            await ctx.send(":pause_button: Paused.")

    @commands.command(aliases = ['clear'], description = 'Deletes all songs in queue')
    async def clearqueue(self,ctx):
        """Clears the song queue"""
        self.songqueue = []
        await ctx.send('The queue has been cleared!')

    @commands.command(aliases = ['purge'], description = 'Shows the songs that are downloaded to local storage')
    async def cache(self,ctx):
        """Shows and deletes songs that are locally stored."""
        dir = os.listdir('./')
        itemlist = []
        for item in dir:
            if item.endswith(('.m4a', 'webm')):
                itemlist.append(os.stat(item).st_size)
        mb = round((sum(itemlist)/(1024*1024)),2)
        await ctx.send(f'There are `{len(itemlist)}` items in local storage, using `{mb}` MB of storage. Would you like to delete them? (`yes`/`no`)')

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        message = await self.bot.wait_for('message', check = check, timeout=30)
        message = message.content
        message = message.strip()
        message = message.lower()
        if message == "yes":
            for item in dir:
                if item.endswith(('.m4a', 'webm')):
                    os.remove(item)
            await ctx.send(f'Deleted `{len(itemlist)}` items from the local storage!')
        else:
            await ctx.send("Didn't get a concrete 'yes', not deleting anything...")

def setup(bot):
    bot.add_cog(Music(bot))
