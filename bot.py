import os
import asyncio
import discord
import traceback
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# ===== INTENTS =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            heartbeat_timeout=60,
            reconnect=True
        )

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        print("✅ Slash commands synced")

bot = MyBot()

# ===== STATUS =====
statuses = [
    discord.Game("24/7 Online"),
    discord.Activity(type=discord.ActivityType.watching, name="the server"),
    discord.Activity(type=discord.ActivityType.listening, name="nothing"),
]

@bot.event
async def on_ready():
    print(f"[ONLINE] {bot.user}")
    if not change_status.is_running():
        change_status.start()

@tasks.loop(minutes=5)
async def change_status():
    activity = statuses[change_status.current_loop % len(statuses)]
    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )

# ===== SLASH COMMAND: /join =====
@bot.tree.command(name="join", description="Gọi bot vào phòng voice của bạn")
async def join(interaction: discord.Interaction):
    user = interaction.user

    if not user.voice:
        await interaction.response.send_message(
            "❌ Bạn chưa ở trong phòng voice",
            ephemeral=True
        )
        return

    channel = user.voice.channel

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()

    await interaction.response.send_message(
        f"✅ Bot đã vào phòng **{channel.name}**"
    )

# ===== SLASH COMMAND: /leave =====
@bot.tree.command(name="leave", description="Cho bot rời phòng voice")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời voice")
    else:
        await interaction.response.send_message(
            "❌ Bot chưa ở trong voice",
            ephemeral=True
        )

# ===== AUTO RESTART =====
async def main():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("❌ BOT CRASH:", e)
            traceback.print_exc()
            await asyncio.sleep(5)

asyncio.run(main())
