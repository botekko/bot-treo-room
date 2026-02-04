import discord
from discord.ext import commands
import os
import threading
from flask import Flask

# ================= Flask (giữ bot online trên Render) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ================= Discord Bot =================
intents = discord.Intents.none()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= Events =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

# ================= Slash command: /join =================
@bot.tree.command(name="join", description="Gọi bot vào phòng voice của bạn")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Bạn phải vào phòng voice trước",
            ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if not vc:
        await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    await interaction.response.send_message(
        f"✅ Bot đang treo ở **{channel.name}**",
        ephemeral=True
    )

# ================= Slash command: /out =================
@bot.tree.command(name="out", description="Cho bot rời phòng voice")
async def out(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect(force=True)
        await interaction.response.send_message(
            "👋 Bot đã rời phòng voice",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Bot không ở phòng nào",
            ephemeral=True
        )

# ================= Run Bot =================
bot.run(os.getenv("TOKEN"))
