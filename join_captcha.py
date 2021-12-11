import discord
from discord.ext import commands, tasks

from claptcha import Claptcha
from random import randint
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.presences = True
command_prefix = "$$"
Villager = commands.Bot(command_prefix=command_prefix, intents=intents)
Conversations = []


# Class used to manage verifications
class VerificationConversation:
    def __init__(self, partner: discord.Member, string: str):
        self.partner = partner
        self.solution = string


# Captcha generation
def generate_image():
    chars = "abcdefghijklmnopqrstuvwxyz123456789"  # Symbols used to generate the image

    # Create the test
    generated_text = ""
    for i in range(6):
        generated_text += chars[randint(0, 34)]

    captcha_image = Claptcha(generated_text, "FreeMono.ttf")  # Create distortion using some module Fungus's code used

    text, file = captcha_image.write('test.png')  # Save the result to file so we can send it
    return text  # Return the correct answer


async def verify(member: discord.Member):
    solution = generate_image()  # Generate a captcha for user

    # Get the captcha image ready
    captcha_image = open('test.png', 'rb')
    captcha_discord = discord.File(captcha_image)

    # Send it to user
    # TODO: This string might need 'c = ' added in front of it. Wait for fungus's response
    await member.send("Welcome to the VillagerRights Discord Server!\n"
                      "Please verify yourself by typing out the characters below!\n"
                      "(Hint: There are no zeroes and all letters are lowercase)", file=captcha_discord)

    Conversations.append(VerificationConversation(member, solution))  # Remember the conversation


# When a user joins send them verification
@Villager.event
async def on_member_join(member):
    await verify(member)


# When we get messaged
@Villager.event
async def on_message(message):
    global sendmessage
    sendmessage = True

    # If message is by the bot itself do nothing
    if message.author.id == 849580883203719168:
        return 0

    if message.author.id == 745652586668884058:
        return 0

    await Villager.process_commands(message)

    # Check if this is from someone we are verifying
    if message.channel.type == discord.ChannelType.private:
        for conversation in Conversations:
            if conversation.partner == message.author:

                # If they got the captcha correct verify them
                if message.content.lower() == conversation.solution:
                    await conversation.partner.send('Thank you, you are now verified.')
                    await conversation.partner.remove_roles(NEW_ROLE, reason='verified')
                    Conversations.remove(conversation)
                    return 0

                # Otherwise, ask them to try again
                else:
                    await conversation.partner.send("Wrong, please try again")

                    Conversations.remove(conversation)  # Nullify this captcha session

                    # Make new captcha for user
                    user = conversation.partner
                    await verify(user)
                    return 1

# COMMANDS
# =======================================================================================


# Ban list
@Villager.command(
    aliases=['BanList', 'BannedUsers', 'Banlist', 'banlist', 'banList', 'bannedusers', 'bannedUsers', 'Bannedusers'])
@commands.has_permissions(ban_members=True)
async def banned_users(ctx):
    ban_list = await ctx.guild.bans()

    # If no-one is banned tell that
    if len(ban_list) == 0:
        banned_users_list = discord.Embed(
            title='Banned Users:',
            description='There are no banned users!',
            colour=discord.Colour.dark_blue()
        )

    # Otherwise, show list of banned users
    else:
        banned_users_list = discord.Embed(
            title='Banned Users:',
            description='Here is a list of banned users',
            colour=discord.Colour.dark_blue()
        )

        # Add all banned users to the list
        for user in ban_list:
            banned_users_list.add_field(name=f'{user[1].name}#{user[1].discriminator}',
                                        value=f'Reason: {user[0]}')

        # Tell how to unban
        banned_users_list.set_footer(text=f'use {command_prefix}unban <name#discriminator> to unban a user')

    # Send the reply
    await ctx.send(embed=banned_users_list)


# Unban a user
@Villager.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, member, *, reason=None):
    found = False
    ban_list = await ctx.guild.bans()

    for user in ban_list:
        if member == f'{user[1].name}#{user[1].discriminator}':
            await ctx.guild.unban(user[1])
            await ctx.send(f'Unbanned [{member.mention}] from your server' if reason is None else
                           f'Unbanned [{member.mention}] from your server with reason: {reason}')
            found = True
            break
    if not found:
        ctx.send(f'No user {member} found in banned users list.')


# Send a test of captcha image
@Villager.command()
async def testmessage(ctx):
    generate_image()  # Create new image

    # Get the captcha image ready
    captcha_image = open('test.png', 'rb')
    captcha_discord = discord.File(captcha_image)

    # Send the message
    await ctx.send("here", file=captcha_discord)


# Ban a user
@Villager.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention}" if reason is None else f'Banned {member.mention}: {reason}')


# This is a weird command I don't really see point in
# But it will be kept as legacy code
@Villager.command()
@commands.has_permissions(ban_members=True)
async def send_it(ctx):
    for member in ctx.guild.members:
        if NEW_ROLE in member.roles:
            await member.send(
                "Hey, basically what happened is that you were kicked because of the new verification process, but feel free to rejoin and verify yourself with this invite code: HzwD8yG")
            await member.kick()


# This seems pointless, but this command sends declaration of villager rights
# I'll just keep it as legacy functionality
@Villager.command()
async def declaration(ctx):
    await ctx.send(
        "Here is The Official Declaration on the Rights of the Villager:\n"
        "https://www.reddit.com/r/villagerrights/comments/ipvejn/the_official_declaration_on_the_rights_of_the/")


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


# Login the bot
with open("token.txt", "r") as f:
    Villager.run(f.readline())
