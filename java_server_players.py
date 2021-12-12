import time

import nextcord
from mcstatus import MinecraftServer
import sqlite3

# For error handling
import socket

# Timekeeping
import datetime

import nextcord as discord
from nextcord.ext import commands, tasks

# Whatever nextcord needs
import logging
logging.basicConfig(level=logging.INFO)

# Configure bot
intents = discord.Intents.default()
intents.members = True
command_prefix = "$$"
VRSMP_bot = commands.Bot(command_prefix=command_prefix, intents=intents)


# Class for saving data to log.
def log(entry):
    f = open('log.txt', 'a')
    f.write(entry + '\n')
    f.close()


@tasks.loop(seconds=15.0)
async def check_java():
    global status_channel
    global online
    global currently_online

    try:

        # Check if server is online and log that
        try:
            server.ping()
            if not online:
                online = True
                log(f'Server went online at {datetime.datetime.now()}')
        except ConnectionResetError or socket.timeout:
            if online:
                online = False
                log(f'Server went offline at {datetime.datetime.now()}')
                currently_online = {}
            return None

        query = server.query()  # Get server data

        # Log players that just connected or disconnected
        for i in query.players.names:
            if i not in currently_online:
                log(f'Player {i} has connected at {datetime.datetime.now()}')
                currently_online[i] = round(time.time())
        for i in currently_online:
            if i not in query.players.names:
                log(f'Player {i} has disconnected at {datetime.datetime.now()}')
                del currently_online[i]

        # Update playtimes
        existing_users = list(map(lambda x: x[0], cur.execute(f"""SELECT * FROM playtimes""").fetchall()))
        for i in currently_online:
            if i in existing_users:
                cur.execute(f"""UPDATE playtimes SET time = time + 15 WHERE username = {i}""")
            else:
                cur.execute("""INSERT INTO playtimes VALUES username=? time=?)""", (i, 15))
        con.commit()

    except Exception as e:
        log(f"System encountered error '{e}' at {datetime.datetime.now()}")

    # Create post
    if online:
        if len(currently_online) > 0:
            status_embed = discord.Embed(
                title="Server is Online",
                description="Here is a list of online players:",
                colour=discord.Colour.dark_blue()
            )

            for user in currently_online:
                status_embed.add_field(name=user, value=f'since <t:{currently_online[user]}:t>')
        else:
            status_embed = discord.Embed(
                title="Server is Online",
                description="There are no online players",
                colour=discord.Colour.dark_blue()
            )

    else:
        status_embed = discord.Embed(
            title="Server is Offline",
            colour=discord.Colour.dark_gray()    # Grey to indicate server being offline
        )

    button = nextcord.ui.Button(label='Server log', style=nextcord.ButtonStyle.link, url='google.com')

    #await status_channel.purge(limit=2)
    await status_channel.send(embed=status_embed, components=[button])


@VRSMP_bot.event
async def on_ready():
    global status_channel
    global online
    global currently_online

    # villager_rights_discord = VRSMP_bot.get_guild(712477764510547969)
    # status_channel = villager_rights_discord.get_channel(770638692901060608)

    villager_rights_discord = VRSMP_bot.get_guild(813237197993148476)
    status_channel = villager_rights_discord.get_channel(875588617156821102)

    online = True  # Whether server is online or not. Used for logging and avoiding error with query.
    currently_online = {}  # ""List"" of currently connected players.

    check_java.start()


if __name__ == '__main__':

    log(f'System went online at {datetime.datetime.now()}')  # Announce system starting up

    # Connect the server
    server = MinecraftServer("villagerrights.xyz")

    # Connect the database
    con = sqlite3.connect('data.db')
    cur = con.cursor()

    # Start the bot
    with open("token.txt", "r") as token:
        VRSMP_bot.run(token.readline())

    log(f'System shutdown at {datetime.datetime.now()}')  # Announce system shutting down
