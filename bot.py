import discord
from discord.ext import commands
import os
import threading
from flask import Flask
from gtts import gTTS
import re
import subprocess
from collections import deque

# ================= Flask (Giữ bot online trên Render) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ================= Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

AUTO_TTS = False
AUDIO_FILE = "tts.mp3"
FFMPEG_PATH = "ffmpeg"

# Kênh chat được phép đọc
TTS_TEXT_CHANNEL_ID = None

# HÀNG ĐỢI TTS (đọc từng câu theo thứ tự)
tts_queue = deque()
is_speaking = False

# ================= Events =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

    try:
        subprocess.check_output([FFMPEG_PATH, "-version"])
        print("✅ FFmpeg đã sẵn sàng!")
    except Exception as e:
        print("❌ Lỗi FFmpeg:", e)

# ================= Slash commands =================
@bot.tree.command(name="join", description="Gọi bot vào phòng voice của bạn")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Bạn cần vào kênh thoại trước!", ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    try:
        if not vc:
            await channel.connect()
        elif vc.channel.id != channel.id:
            await vc.move_to(channel)
    except Exception:
        if vc:
            await vc.disconnect(force=True)
        await channel.connect()

    await interaction.response.send_message(
        f"✅ Bot đã vào phòng **{channel.name}**", ephemeral=True
    )

@bot.tree.command(name="auto", description="Bật chế độ tự động đọc tin nhắn")
async def auto(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = True
    await interaction.response.send_message(
        "🔊 Đã BẬT chế độ tự động đọc.", ephemeral=True
    )

@bot.tree.command(name="tat", description="Tắt chế độ tự động đọc tin nhắn")
async def tat(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = False
    await interaction.response.send_message(
        "🔇 Đã TẮT chế độ tự động đọc.", ephemeral=True
    )

@bot.tree.command(name="out", description="Đá bot ra khỏi phòng và reset kết nối")
async def out(interaction: discord.Interaction):
    global tts_queue, is_speaking
    if interaction.guild.voice_client:
        tts_queue.clear()
        is_speaking = False
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message(
            "👋 Đã reset bot. Hãy gọi lại `/join` hoặc `/noi`",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Bot không ở trong phòng nào.", ephemeral=True
        )

@bot.tree.command(name="noi", description="Bot vào voice và nói văn bản bạn nhập")
async def noi(interaction: discord.Interaction, text: str):
    global TTS_TEXT_CHANNEL_ID
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send(
            "❌ Bạn cần vào kênh thoại trước!", ephemeral=True
        )
        return

    TTS_TEXT_CHANNEL_ID = interaction.channel.id

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    try:
        if not vc:
            vc = await channel.connect()
        elif vc.channel.id != channel.id:
            await vc.move_to(channel)
    except Exception:
        if vc:
            await vc.disconnect(force=True)
        vc = await channel.connect()

    add_to_queue(vc, text)
    await interaction.followup.send(
        f"🗣️ Đã thêm vào hàng đợi: {text}", ephemeral=True
    )

@bot.tree.command(name="skip", description="Bỏ qua câu bot đang đọc")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if not vc or not vc.is_playing():
        await interaction.response.send_message(
            "❌ Bot không đang nói.", ephemeral=True
        )
        return

    if not interaction.user.voice or interaction.user.voice.channel != vc.channel:
        await interaction.response.send_message(
            "❌ Bạn phải ở cùng phòng voice với bot.", ephemeral=True
        )
        return

    vc.stop()
    await interaction.response.send_message("⏭️ Đã skip.", ephemeral=True)

# ================= TTS Processing =================
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"<@!?\d+>", "", text)
    text = re.sub(r"<#\d+>", "", text)
    text = re.sub(r"<@&\d+>", "", text)
    text = re.sub(r"<:.+?:\d+>", "", text)

    match = re.search(r"\d{5,}", text)
    if match:
        text = text[:match.start()]

    text = re.sub(r"[^\w\sÀ-ỹ]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def add_to_queue(vc, text):
    global is_speaking
    text = clean_text(text)
    if not text:
        return

    tts_queue.append((vc, text))
    if not is_speaking:
        play_next()

def play_next():
    global is_speaking

    if not tts_queue:
        is_speaking = False
        return

    is_speaking = True
    vc, text = tts_queue.popleft()

    try:
        tts = gTTS(text=text, lang="vi")
        tts.save(AUDIO_FILE)

        source = discord.FFmpegPCMAudio(
            AUDIO_FILE,
            executable=FFMPEG_PATH,
            before_options="-loglevel quiet",
            options="-vn"
        )

        def after_play(error):
            bot.loop.call_soon_threadsafe(play_next)

        vc.play(source, after=after_play)

    except Exception as e:
        print("❌ Lỗi TTS:", e)
        play_next()

# ================= Auto TTS Logic =================
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot or not AUTO_TTS:
        return

    if not message.guild:
        return

    if message.attachments or message.embeds:
        return

    if TTS_TEXT_CHANNEL_ID is None or message.channel.id != TTS_TEXT_CHANNEL_ID:
        return

    vc = message.guild.voice_client

    if not vc or not message.author.voice or message.author.voice.channel != vc.channel:
        return

    if not message.content.strip():
        return

    add_to_queue(vc, message.content)

# ================= Run Bot =================
bot.run(os.getenv("TOKEN"))
