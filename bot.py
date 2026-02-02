import os
import asyncio
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("24/7 Online")
    )
    print(f"[ONLINE] {bot.user}")

@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn chưa ở trong phòng voice")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"✅ Bot đã vào phòng **{channel.name}**")

async def runner():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("[RECONNECT]", e)
            await asyncio.sleep(10)

asyncio.run(runner())
