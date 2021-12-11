from mcstatus import MinecraftServer
import sqlite3

# For error handling
import socket

# Timekeeping
import datetime
import time

import discord
from discord.ext import commands, tasks


intents = discord.Intents.default()
intents.members = True
intents.presences = True
command_prefix = "$$"
VRSMP_bot = commands.Bot(command_prefix=command_prefix, intents=intents)


# Class for saving data to log.
def log(entry):
    f = open('log.txt', 'a')
    f.write(entry + '\n')
    f.close()


@tasks.loop(seconds=15.0)
async def check_java():
    global VILLAGER_RIGHTS
    global STATUS_CHANNEL
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
                currently_online[i] = datetime.datetime.now()
        for i in currently_online:
            if i not in query.players.names:
                log(f'Player {i} has disconnected at {datetime.datetime.now()}')
                currently_online.remove(i)

        currently_online = query.players.names  # Update currently online players

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


    if online:
        if len(currently_online) > 0:
            status_embed = discord.Embed(
                title="Server is Online",
                description="Here is a list of online players:",
                colour=discord.Colour.dark_blue()
            )

            for user in currently_online:
                status_embed.add_field(name=user, value=f'since {currently_online[user]}')
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

    await STATUS_CHANNEL.purge(limit=2)
    await STATUS_CHANNEL.send(embed=status_embed)

@VRSMP_bot.event
async def on_ready():
    global VILLAGER_RIGHTS
    global STATUS_CHANNEL
    global online
    global currently_online

    # VILLAGER_RIGHTS = VRSMP_bot.get_guild(712477764510547969)
    # STATUS_CHANNEL = VILLAGER_RIGHTS.get_channel(770638692901060608)

    VILLAGER_RIGHTS = VRSMP_bot.get_guild(813237197993148476)
    STATUS_CHANNEL = VILLAGER_RIGHTS.get_channel(875588617156821102)

    online = True  # Whether server is online or not. Used for logging and avoiding error with query.
    currently_online = {}  # ""List"" of currently connected players.

    check_java.start()


if __name__ == '__main__':

    log(f'System went online at {datetime.datetime.now()}')  # Announce system starting up

    # Connect some constants
    server = MinecraftServer("villagerrights.xyz")

    con = sqlite3.connect('data.db')
    cur = con.cursor()

    # Login the bot
    with open("token.txt", "r") as f:
        VRSMP_bot.run(f.readline())

    log(f'System shutdown at {datetime.datetime.now()}')  # Announce system shutting down
