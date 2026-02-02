import os
import asyncio
import discord
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.none()
bot = commands.Bot(command_prefix="!", intents=intents)

statuses = [
    discord.Game("24/7 Online"),
    discord.Activity(type=discord.ActivityType.watching, name="the server"),
    discord.Game("AFK Bot"),
    discord.Activity(type=discord.ActivityType.listening, name="nothing"),
]

@bot.event
async def on_ready():
    print(f"[ONLINE] {bot.user}")
    change_status.start()

@tasks.loop(minutes=5)
async def change_status():
    await bot.change_presence(activity=statuses[change_status.current_loop % len(statuses)])

async def runner():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("[RECONNECT]", e)
            await asyncio.sleep(10)

asyncio.run(runner())
