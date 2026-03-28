import discord
import json
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

COMMANDS_FILE = "commands.json"


def load_custom_commands():
    if not os.path.exists(COMMANDS_FILE):
        return {}
    with open(COMMANDS_FILE, "r") as f:
        return json.load(f)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        trigger = message.content[1:].lower().strip()
        custom_cmds = load_custom_commands()
        if trigger in custom_cmds:
            await message.channel.send(custom_cmds[trigger])
            return

    await bot.process_commands(message)


@bot.command(name="help")
async def help_command(ctx):
    custom_cmds = load_custom_commands()
    if not custom_cmds:
        await ctx.send("No custom commands yet.")
        return
    lines = [f"`!{cmd}` — {resp}" for cmd, resp in custom_cmds.items()]
    await ctx.send("**Available commands:**\n" + "\n".join(lines))


bot.run(os.getenv("DISCORD_TOKEN"))
