import datetime  # Timekeeping
import logging
import socket  # For error handling
import sqlite3  # Database
import time  # For getting unix timestamp

import nextcord
import nextcord as discord
import requests
from mcstatus import MinecraftServer
from nextcord.ext import commands, tasks

logging.basicConfig(level=logging.INFO)

# Configure the bot
intents = discord.Intents.default()
intents.members = True  # IDK what this does tbh
command_prefix = "$"
VRSMP_bot = commands.Bot(command_prefix=command_prefix, intents=intents)


# Class for saving data to log.
def log(entry):
    f = open('log.txt', 'a')
    f.write(entry + '\n')
    f.close()


# Function that returns uuid of a user by nick. So that the db doesn't break from someone changing their username.
def get_id(user):
    url = f'https://api.mojang.com/users/profiles/minecraft/{user}?'
    response = requests.get(url)
    uuid = response.json()['id']
    return uuid


# Command for showing info about a player
@VRSMP_bot.command(aliases=['Player', 'Player_info', 'player_info'])
async def player(ctx, *, player_name):
    global currently_online

    player_name = str(player_name)  # Just in case...

    # Try getting uuid. If we fail then user doesn't exist.
    try:
        database_user = cur.execute(f"""SELECT * FROM Users WHERE uuid='{get_id(player_name)}'""").fetchall()
    except:
        notfound_embed = discord.Embed(
            title=f"Player {player_name} doesn't exist",
            description="Well, according to Mojang at least. \nPlease check you spelling.",
            colour=discord.Colour.dark_red()
        )
        await ctx.send(embed=notfound_embed)
        return 0

    # If the player isn't in the database
    if len(database_user) == 0:
        player_info = discord.Embed(
            title=f"Player {player_name} not found in the database",
            description="Please check you spelling",
            colour=discord.Colour.dark_red()
        )

    # If we found the player show our info about them
    else:
        player_info = discord.Embed(
            title=f"Info about player {player_name}",
            colour=discord.Colour.dark_green()
        )

        # Set their skin's head as embed thumbnail which makes it looks fancy
        player_info.set_thumbnail(url=f'https://crafatar.com/avatars/{get_id(player_name)}')

        # Show all info we have on the user

        player_info.add_field(name="Time played:",
                              value=f"{time.strftime('%H:%M:%S', time.gmtime(int(database_user[0][1])))}")
        if player_name in currently_online:
            player_info.add_field(name="This player is online right now",
                                  value=f'since <t:{currently_online[player_name]}:t>')
        else:
            player_info.add_field(name="Last seen:", value=f"<t:{int(database_user[0][2])}>")
        player_info.add_field(name="First seen:", value=f"<t:{int(database_user[0][3])}>")

    await ctx.send(embed=player_info)


@tasks.loop(seconds=15.0)
async def check_java():
    global status_channel
    global online
    global currently_online
    global msg

    try:

        # Check if server is online
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

        query = server.query()  # Get server query)

        # Update list of currently online players
        for i in query.players.names:
            if i not in currently_online:
                currently_online[i] = round(time.time())
                log(f'Player {i} has connected at {datetime.datetime.now()}')
        for i in currently_online:
            if i not in query.players.names:
                del currently_online[i]
                log(f'Player {i} has disconnected at {datetime.datetime.now()}')

        # Update playtimes
        existing_users = list(map(lambda x: x[0], cur.execute(f"""SELECT * FROM Users""").fetchall()))
        for i in currently_online:
            if get_id(i) in existing_users:
                cur.execute(f"""UPDATE Users SET time = time + 15 WHERE uuid='{get_id(i)}'""")
                cur.execute(f"""UPDATE Users SET last_seen = {time.time()} WHERE uuid='{get_id(i)}'""")
            else:
                cur.execute("""INSERT INTO Users(uuid, time, last_seen, first_seen) VALUES (?, ?, ?, ?)""",
                            (get_id(i), 15, time.time(), time.time()))
        con.commit()

    except Exception as e:
        log(f"System encountered error '{e}' at {datetime.datetime.now()}")

    # Show the list in the channel
    if online:

        # Server online, there are players
        if len(currently_online) > 0:
            status_embed = discord.Embed(
                title="Server is Online",
                description="Here is a list of online players:",
                colour=discord.Colour.dark_blue()
            )

            for user in currently_online:
                status_embed.add_field(name=user, value=f'since <t:{currently_online[user]}:t>')

        # Server online, no players
        else:
            status_embed = discord.Embed(
                title="Server is Online",
                description="There are no online players",
                colour=discord.Colour.dark_blue()
            )

    # Server offline
    else:
        status_embed = discord.Embed(
            title="Server is Offline",
            colour=discord.Colour.dark_gray()    # Grey to indicate server being offline
        )

    status_embed.set_footer(text='Use "$Player [username]" to get info about a player')  # Hint for some people
    status_embed.timestamp = datetime.datetime.now()  # Show when it was last updated

    # try editing existing message. If for some reason we can't edit it just create a new one
    try:
        await msg.edit(embed=status_embed)
    except:
        await status_channel.purge(limit=2)
        await status_channel.send(embed=status_embed)


@VRSMP_bot.event
async def on_ready():
    global status_channel
    global online
    global currently_online
    global msg

    # villager_rights_discord = VRSMP_bot.get_guild(712477764510547969)
    # status_channel = villager_rights_discord.get_channel(770638692901060608)

    villager_rights_discord = VRSMP_bot.get_guild(693125394228052079)
    status_channel = villager_rights_discord.get_channel(919944776122503188)

    online = True  # Whether server is online or not. Used for logging and avoiding error with query.
    currently_online = {}  # ""List"" of currently connected players.

    # Prepare message so that we can edit it
    await status_channel.purge(limit=2)
    startup_embed = discord.Embed(title='Bot is starting up', description='Check again in a few seconds')
    msg = await status_channel.send(embed=startup_embed)

    check_java.start()


if __name__ == '__main__':

    # Connect the server
    server = MinecraftServer("villagerrights.xyz")

    # Connect the database
    con = sqlite3.connect('data.db')
    cur = con.cursor()

    # Start the bot
    with open("token.txt", "r") as token:
        VRSMP_bot.run(token.readline())
