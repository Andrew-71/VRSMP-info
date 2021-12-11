import discord
from discord.ext import commands, tasks
from claptcha import Claptcha
from random import randint
from mcstatus import MinecraftServer
from datetime import datetime

Java_Server = MinecraftServer.lookup("villagerrights.xyz:25565")
Current_Players = []
intents = discord.Intents.default()
intents.members = True
intents.presences = True
command_prefix = "$$"
Villager = commands.Bot(command_prefix=command_prefix, intents=intents)

Conversations = []


class VerificationConversation:
    def __init__(self, partner: discord.Member, string: str):
        self.partner = partner
        self.solution = string


async def verify(member: discord.Member):
    solution = generate_image()
    a = open("test.png", "rb")
    b = discord.File(a)
    c = await member.send("Welcome to the VillagerRights Discord Server! Please verify yourself by typing out the characters below! (Hint: There are no zeroes)", file=b)
    d = VerificationConversation(member, solution)
    Conversations.append(d)


def generate_image():
    p = ""
    chars = "abcdefghijklmnopqrstuvwxyz123456789"
    for i in range(6):
        v = randint(0, 34)
        p += chars[v]

    c = Claptcha(p, "FreeMono.ttf")

    text, file = c.write('test.png')

    return text


@Villager.event
async def on_member_join(member):
    await verify(member)


@Villager.event
async def on_ready():

    global VILLAGER_RIGHTS

    global NEW_ROLE

    global STATUS_CHANNEL

    print(discord.__version__)
    print("ready")
    VILLAGER_RIGHTS = Villager.get_guild(712477764510547969)
    NEW_ROLE = VILLAGER_RIGHTS.get_role(742825059697164318)
    STATUS_CHANNEL = VILLAGER_RIGHTS.get_channel(770638692901060608)

    @tasks.loop(seconds=15.0)
    async def check_java():

        try:
            a = Java_Server.query()
            b = a.players.names
            online = True
        except ConnectionResetError:
            online = False
        if online:
            for tupl in Current_Players:
                if tupl[0] in b:
                    continue
                else:
                    Current_Players.remove(tupl)
            if len(b) > 0:
                Status_Embed = discord.Embed(
                    title="Server is Online",
                    description="Here is a list of online players",
                    colour=discord.Colour.blue()
                )
                for player in b:
                    inlist = False
                    for tup in Current_Players:
                        if tup[0] == player:
                            inlist = True
                            x = tup[1]
                            break
                    if not inlist:
                        x = datetime.now().strftime("%X")
                        Current_Players.append((player, x))
                Status_Embed.add_field(name=player, value=f"since {x}")


            else:
                Status_Embed = discord.Embed(
                    title="Server is Online",
                    description="There are no online players",
                    colour=discord.Colour.blue()
                )
        else:
            Status_Embed = discord.Embed(
                title="Server is Offline",
                colour=discord.Colour.blue()
            )
        await STATUS_CHANNEL.purge(limit=2)
        await STATUS_CHANNEL.send(embed=Status_Embed)
    check_java.start()


@Villager.event
async def on_message(message):
    global sendmessage
    sendmessage = True
    if message.author.id == 745652586668884058:
        return 0
    await Villager.process_commands(message)
    if message.channel.type == discord.ChannelType.private:
        for conversation in Conversations:
            if conversation.partner == message.author:
                if message.content.lower() == conversation.solution:
                    await conversation.partner.send("Thank you, you are now verified.")
                    await conversation.partner.remove_roles(NEW_ROLE, reason="verified")
                    Conversations.remove(conversation)
                    return 0
                else:
                    await conversation.partner.send("Wrong, please try again")
                    abx = conversation.partner
                    Conversations.remove(conversation)
                    await verify(abx)
                    return 1


@Villager.command(
    aliases=['BanList', 'BannedUsers', 'Banlist', 'banlist', 'banList', 'bannedusers', 'bannedUsers', 'Bannedusers'])
@commands.has_permissions(ban_members=True)
async def banned_users(ctx):
    BanList = await ctx.guild.bans()
    if len(BanList) == 0:
        bannedUserList = discord.Embed(
            title='Banned Users:',
            description='There are no banned users!',
            colour=discord.Colour.blue()
        )
    else:
        bannedUserList = discord.Embed(
            title='Banned Users:',
            description='Here is a list of banned users',
            colour=discord.Colour.blue()
        )
        for p in range(len(BanList)):
            bannedUserList.add_field(name=f'{BanList[p][1].name}#{BanList[p][1].discriminator}',
                                     value=f'Reason: {BanList[p][0]}')
        bannedUserList.set_footer(text=f'use {command_prefix}unban <name#discriminator> to unban a user')
    await ctx.send(embed=bannedUserList)


@Villager.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, member, *, reason=None):
    count = 0
    banList = await ctx.guild.bans()
    for x in range(len(banList)):
        if member == f"{banList[x][1].name}#{banList[x][1].discriminator}":
            await ctx.guild.unban(banList[x][1])
            await ctx.send(f"Unbanned [{member.mention}] from your server with reason: {reason}")
            count += 1
    if count == 0:
        ctx.send(f"No user {member} found in banned users list!")
        return


@Villager.command()
async def testmessage(ctx):
    testText = generate_image()
    c = open("test.png", "rb")
    a = discord.File(c)
    await ctx.send("here", file=a)


@Villager.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention}" if reason is None else f'Banned {member.mention}: {reason}')


@Villager.command()
@commands.has_permissions(ban_members=True)
async def send_it(ctx):
    for member in ctx.guild.members:
        if NEW_ROLE in member.roles:
            await member.send("Hey, basically what happened is that you were kicked because of the new verification process, but feel free to rejoin and verify yourself with this invite code: HzwD8yG")
            await member.kick()


@Villager.command()
async def declaration(ctx):
    await ctx.send("https://www.reddit.com/r/villagerrights/comments/ipvejn/the_official_declaration_on_the_rights_of_the/")

with open("../token.txt", "r") as f:
    
    Villager.run(f.readline())



