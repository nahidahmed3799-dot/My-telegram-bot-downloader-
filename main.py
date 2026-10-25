# -*- coding: utf-8 -*-
import os, re, time, threading, asyncio
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

app = Flask(__name__)

@app.route("/")
def home():
    return "Universal Downloader Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

API_ID = 31609403
API_HASH = "4a320ca3258d0171b477266910c10a75"
BOT_TOKEN = "8639277798:AAEUOM5lt1TnW4b-Hnf_XpO3dFSiEitg_Mg"
CHANNEL_TAG = "@UniversalDownloaderProBot"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

session_string = os.environ.get("USER_SESSION_B64", "").strip()

bot = TelegramClient("bot_session", API_ID, API_HASH)
user_bot = TelegramClient(StringSession(session_string), API_ID, API_HASH) if session_string else None

async def progress_callback(current, total, event, status_msg, action_name, start_time):
    now = time.time()
    diff = now - start_time
    if diff >= 3:
        percent = (current / total) * 100
        speed = current / (diff * 1024 * 1024)
        try:
            txt = f"{action_name}: {round(percent, 1)}% | Speed: {round(speed, 2)} MB/s"
            await status_msg.edit(txt)
        except Exception:
            pass

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await event.respond("⚡ <b>Universal Downloader Bot Online!</b>\nযেকোনো পাবলিক বা প্রাইভেট লিঙ্ক পাঠান।", parse_mode="html")

@bot.on(events.NewMessage)
async def message_handler(event):
    raw = event.raw_text.strip()
    if not raw or raw.startswith("/"):
        return
    if "t.me/" in raw:
        if not user_bot:
            return await event.respond("❌ ইউজার সেশন সেট করা নেই!")

        match_single = re.search(r"https://t\.me/(?:c/)?([^/]+)/(\d+)", raw)
        if not match_single:
            return
        raw_channel = match_single.group(1)
        start_id = int(match_single.group(2))
        status = await event.respond("🔍 মিডিয়া খোঁজা হচ্ছে...")
        try:
            target_chat = None
            if raw_channel.isdigit():
                c_id = int(raw_channel)
                for cid in [int(f"-100{c_id}"), c_id]:
                    try:
                        target_chat = await user_bot.get_entity(cid)
                        if target_chat:
                            break
                    except Exception:
                        pass
                if not target_chat:
                    async for d in user_bot.iter_dialogs():
                        if str(c_id) in str(d.id):
                            target_chat = d.entity
                            break
            else:
                target_chat = await user_bot.get_entity(raw_channel)

            if not target_chat:
                return await status.edit("❌ চ্যানেলে অ্যাক্সেস নেই!")

            msg = await user_bot.get_messages(target_chat, ids=start_id)
            if not msg:
                return await status.edit("❌ পোস্ট পাওয়া যায়নি!")

            msgs_to_dl = [msg]
            if msg.grouped_id:
                nearby = await user_bot.get_messages(target_chat, limit=20, min_id=max(1, start_id - 10), max_id=start_id + 10)
                album = [m for m in nearby if m.grouped_id == msg.grouped_id]
                if album:
                    msgs_to_dl = sorted(album, key=lambda x: x.id)

            for idx, m in enumerate(msgs_to_dl, 1):
                if m.media or m.file:
                    await status.edit(f"⬇️ ডাউনলোড হচ্ছে ({idx}/{len(msgs_to_dl)})...")
                    fpath = await user_bot.download_media(m, file=DOWNLOAD_DIR)
                    if fpath and os.path.exists(fpath):
                        st_up = time.time()
                        await bot.send_file(
                            event.chat_id,
                            fpath,
                            caption=f"⚡ Downloaded via {CHANNEL_TAG}",
                            force_document=True,
                            progress_callback=lambda c, t: progress_callback(c, t, event, status, "⬆️ আপলোড হচ্ছে", st_up)
                        )
                        os.remove(fpath)
            await status.delete()
        except Exception as e:
            await status.edit(f"❌ ত্রুটি: {str(e)}")

async def start_services():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    if user_bot:
        try:
            await user_bot.connect()
            if not await user_bot.is_user_authorized():
                print("Warning: User session unauthorized!")
            else:
                print("✅ User account connected successfully!")
        except Exception as e:
            print(f"User bot connect error: {e}")

    await bot.start(bot_token=BOT_TOKEN)
    print("Bot is alive and running!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_services())
    finally:
        loop.close()
