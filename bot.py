import os
import threading
import asyncio
import discord
from discord.ext import commands
from flask import Flask

# ===== Flask fake server (để Render khỏi kill) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ===== Discord bot =====
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

async def start_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("[RECONNECT]", e)
            await asyncio.sleep(10)

# ===== Chạy song song =====
threading.Thread(target=run_web).start()
asyncio.run(start_bot())
