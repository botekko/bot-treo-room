import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# ===================== ENV =====================
TOKEN = os.getenv("TOKEN_DISCORD_BOT")  # ĐÚNG với Render
if not TOKEN:
    raise RuntimeError("❌ Chưa set TOKEN_DISCORD_BOT trong Render Environment")

# ===================== Flask keep-alive =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ===================== Discord intents =====================
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== Auto rejoin =====================
AUTO_REJOIN_CHANNEL_ID: int | None = None

# ===================== Events =====================
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Slash sync error:", e)

    print(f"✅ Bot online: {bot.user}")

# ===================== /join =====================
@bot.tree.command(name="join", description="Gọi bot vào phòng voice của bạn")
async def join(interaction: discord.Interaction):
    global AUTO_REJOIN_CHANNEL_ID

    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Bạn phải vào voice trước",
            ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    AUTO_REJOIN_CHANNEL_ID = channel.id

    vc = interaction.guild.voice_client

    try:
        if not vc:
            await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Không vào được voice: {e}",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"✅ Bot đang treo ở **{channel.name}** (auto rejoin bật)",
        ephemeral=True
    )

# ===================== /out =====================
@bot.tree.command(name="out", description="Cho bot rời phòng voice")
async def out(interaction: discord.Interaction):
    global AUTO_REJOIN_CHANNEL_ID

    vc = interaction.guild.voice_client
    AUTO_REJOIN_CHANNEL_ID = None

    if vc:
        await vc.disconnect(force=True)
        await interaction.response.send_message(
            "👋 Bot đã rời phòng (auto rejoin tắt)",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Bot không ở phòng nào",
            ephemeral=True
        )

# ===================== Auto rejoin khi bị kick =====================
@bot.event
async def on_voice_state_update(member, before, after):
    if not bot.user or member.id != bot.user.id:
        return

    if before.channel and after.channel is None:
        if AUTO_REJOIN_CHANNEL_ID:
            channel = bot.get_channel(AUTO_REJOIN_CHANNEL_ID)
            if channel:
                try:
                    await channel.connect()
                    print("🔁 Auto rejoin thành công")
                except Exception as e:
                    print("❌ Auto rejoin lỗi:", e)

# ===================== RUN BOT =====================
bot.run(TOKEN, reconnect=True)
