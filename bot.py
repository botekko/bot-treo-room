import os
import asyncio
import discord
import traceback
from discord.ext import commands, tasks

# ===== TOKEN =====
TOKEN = os.getenv("DISCORD_TOKEN")  # Render / VPS
# TOKEN = "PASTE_TOKEN_HERE"        # Test local

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    heartbeat_timeout=60,
    reconnect=True
)

# ===== STATUS LIST =====
statuses = [
    discord.Game("24/7 Online"),
    discord.Activity(type=discord.ActivityType.watching, name="the server"),
    discord.Game("AFK Bot"),
    discord.Activity(type=discord.ActivityType.listening, name="nothing"),
]

# ===== READY =====
@bot.event
async def on_ready():
    print(f"[ONLINE] {bot.user}")
    if not change_status.is_running():
        change_status.start()

# ===== STATUS LOOP =====
@tasks.loop(minutes=5)
async def change_status():
    activity = statuses[change_status.current_loop % len(statuses)]
    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )

# ===== JOIN VOICE =====
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

# ===== LEAVE VOICE =====
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot đã rời voice")

# ===== AUTO RESTART KHI CRASH =====
async def main():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("❌ BOT CRASH:", e)
            traceback.print_exc()
            await asyncio.sleep(5)

asyncio.run(main())
