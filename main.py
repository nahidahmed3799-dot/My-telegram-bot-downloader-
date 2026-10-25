# -*- coding: utf-8 -*-
import os, re, time, threading, asyncio, datetime
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# UptimeRobot / Render 24/7 Server
app = Flask(__name__)

@app.route("/")
def home():
    return "Universal Downloader Pro Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# API Credentials & Settings
API_ID = 31609403
API_HASH = "4a320ca3258d0171b477266910c10a75"
BOT_TOKEN = "8639277798:AAEUOM5lt1TnW4b-Hnf_XpO3dFSiEitg_Mg"
CHANNEL_TAG = "@UniversalDownloaderProBot"
DOWNLOAD_DIR = "downloads"
THUMB_DIR = "thumbnails"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

START_TIME = time.time()
BOT_STATS = {"downloads": 0, "total_mb": 0.0, "users": set()}
USER_STATS = {}  # {user_id: {"downloads": 0, "mb": 0.0}}

session_string = os.environ.get("USER_SESSION_B64", "").strip()
bot = TelegramClient("bot_session", API_ID, API_HASH)
user_bot = TelegramClient(StringSession(session_string), API_ID, API_HASH) if session_string else None

START_BUTTONS = [
    [Button.inline("👑 Owner Support", data="owner_support")],
    [Button.inline("🏆 Leaderboard", data="leaderboard")],
    [Button.inline("📊 My Stats", data="my_stats")],
    [Button.inline("⚡ Quick Dashboard", data="quick_dashboard")],
    [Button.inline("🖥️ Server Status", data="server_status")],
    [Button.inline("⚡ Ping & Latency", data="ping_latency")],
    [Button.inline("⚙️ Settings", data="settings")],
    [Button.inline("📖 Help", data="help_info")],
    [Button.inline("🖼️ /thumb", data="thumb_info")]
]

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{round(size, 2)} {unit}"
        size /= 1024.0
    return f"{round(size, 2)} TB"

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

@bot.on(events.NewMessage(pattern=r"^/start$"))
async def start_handler(event):
    uid = event.sender_id
    BOT_STATS["users"].add(uid)
    text = (
        "⚡ <b>Universal Downloader Bot Online!</b>\n"
        "যেকোনো পাবলিক বা প্রাইভেট লিঙ্ক পাঠান।"
    )
    await event.respond(text, parse_mode="html", buttons=START_BUTTONS)

@bot.on(events.NewMessage(pattern=r"^/thumb$"))
async def thumb_cmd_handler(event):
    if not event.reply_to_msg_id:
        return await event.respond("🖼️ কোনো ছবিতে রিপ্লাই দিয়ে <code>/thumb</code> লিখুন কাস্টম থাম্বনেইল সেট করার জন্য।", parse_mode="html")
    reply = await event.get_reply_message()
    if reply.photo:
        tpath = os.path.join(THUMB_DIR, f"{event.sender_id}.jpg")
        await reply.download_media(file=tpath)
        await event.respond("✅ <b>কাস্টম থাম্বনেইল সফলভাবে সেট করা হয়েছে!</b>", parse_mode="html")
    else:
        await event.respond("❌ অনুগ্রহ করে কোনো ছবির ওপর রিপ্লাই দিন।")

@bot.on(events.NewMessage(pattern=r"^/delthumb$"))
async def delthumb_cmd(event):
    tpath = os.path.join(THUMB_DIR, f"{event.sender_id}.jpg")
    if os.path.exists(tpath):
        os.remove(tpath)
        await event.respond("🗑️ আপনার থাম্বনেইল ডিলিট করা হয়েছে।")
    else:
        await event.respond("❌ আপনার কোনো থাম্বনেইল সেভ করা নেই।")

@bot.on(events.NewMessage(pattern=r"^/showthumb$"))
async def showthumb_cmd(event):
    tpath = os.path.join(THUMB_DIR, f"{event.sender_id}.jpg")
    if os.path.exists(tpath):
        await bot.send_file(event.chat_id, tpath, caption="🖼️ আপনার বর্তমান কাস্টম থাম্বনেইল")
    else:
        await event.respond("❌ আপনার কোনো কাস্টম থাম্বনেইল সেট করা নেই।")

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")
    uid = event.sender_id

    if data == "owner_support":
        await event.respond("👑 <b>এডমিন সাপোর্ট:</b>\nবটের যেকোনো সমস্যা বা ফিডব্যাকের জন্য এডমিনের সাথে যোগাযোগ করুন।\nঅফিসিয়াল চ্যানেল: " + CHANNEL_TAG, parse_mode="html")
        await event.answer()

    elif data == "leaderboard":
        if not USER_STATS:
            txt = "🏆 <b>টপ ডাউনলোডার লিডারবোর্ড:</b>\n\nএখনো কোনো রেকর্ড নেই!"
        else:
            sorted_users = sorted(USER_STATS.items(), key=lambda x: x[1]["downloads"], reverse=True)[:5]
            txt = "🏆 <b>টপ ডাউনলোডার লিডারবোর্ড:</b>\n\n"
            for rank, (u_id, st) in enumerate(sorted_users, 1):
                txt += f"{rank}. ইউজার ID: <code>{u_id}</code> | মোট: {st['downloads']} ফাইল ({round(st['mb'], 2)} MB)\n"
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "my_stats":
        u_info = USER_STATS.get(uid, {"downloads": 0, "mb": 0.0})
        txt = (
            f"📊 <b>আপনার ব্যক্তিগত পরিসংখ্যান:</b>\n\n"
            f"👤 ইউজার ID: <code>{uid}</code>\n"
            f"📥 মোট ডাউনলোড: <b>{u_info['downloads']} টি ফাইল</b>\n"
            f"💾 ব্যবহৃত ডাটা: <b>{round(u_info['mb'], 2)} MB</b>"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "quick_dashboard":
        uptime_sec = int(time.time() - START_TIME)
        uptime = str(datetime.timedelta(seconds=uptime_sec))
        txt = (
            f"⚡ <b>কুইক ড্যাশবোর্ড:</b>\n\n"
            f"⏱️ বটের আপটাইম: <b>{uptime}</b>\n"
            f"👥 মোট সক্রিয় ইউজার: <b>{len(BOT_STATS['users'])} জন</b>\n"
            f"📦 সম্পূর্ণ প্রসেসড মিডিয়া: <b>{BOT_STATS['downloads']} টি</b>\n"
            f"🚀 নেটওয়ার্ক ইঞ্জিন: <b>Telethon MTProto + Cloud Worker</b>"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "server_status":
        txt = (
            "🖥️ <b>সার্ভার স্ট্যাটাস:</b>\n\n"
            "🟢 সার্ভার অবস্থা: <b>24/7 Live</b>\n"
            "☁️ হোস্টিং প্ল্যাটফর্ম: <b>Render Cloud</b>\n"
            "🛡️ মোড: <b>High Speed MTProto Stream</b>"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "ping_latency":
        st = time.time()
        m = await event.respond("⚡ লেটেন্সি পরিমাপ করা হচ্ছে...")
        latency = round((time.time() - st) * 1000)
        await m.edit(f"⚡ <b>পিং ও লেটেন্সি:</b> <code>{latency} ms</code>", parse_mode="html")
        await event.answer()

    elif data == "settings":
        tpath = os.path.join(THUMB_DIR, f"{uid}.jpg")
        has_thumb = "সেট করা আছে ✅" if os.path.exists(tpath) else "ডিফল্ট ❌"
        txt = (
            f"⚙️ <b>বট সেটিংস:</b>\n\n"
            f"🖼️ কাস্টম থাম্বনেইল: <b>{has_thumb}</b>\n"
            f"⚡ স্পিড মোড: <b>Ultra High Boost</b>\n"
            f"📁 রিসিভ ফরম্যাট: <b>অরিজিনাল ডক/ভিডিও</b>"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "help_info":
        txt = (
            "📖 <b>ব্যবহার নির্দেশিকা:</b>\n\n"
            "১. পাবলিক বা প্রাইভেট চ্যানেলের যেকোনো পোস্টের লিঙ্ক সরাসরি পাঠিয়ে দিন।\n"
            "২. প্রাইভেট চ্যানেল ডাউনলোডের জন্য ইউজার অ্যাকাউন্টের চ্যানেলে জয়েন থাকা বাধ্যতামূলক।\n"
            "৩. থাম্বনেইল সেট করতে ছবি পাঠিয়ে ক্যাপশনে <code>/thumb</code> লিখুন।"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

    elif data == "thumb_info":
        txt = (
            "🖼️ <b>থাম্বনেইল কমান্ডসমূহ:</b>\n\n"
            "• <code>/thumb</code> - ছবির রিপ্লাই দিয়ে সেট করুন\n"
            "• <code>/showthumb</code> - বর্তমান থাম্বনেইল দেখুন\n"
            "• <code>/delthumb</code> - থাম্বনেইল মুছে ফেলুন"
        )
        await event.respond(txt, parse_mode="html")
        await event.answer()

@bot.on(events.NewMessage)
async def message_handler(event):
    raw = event.raw_text.strip()
    if not raw or raw.startswith("/"):
        return

    if "t.me/" in raw:
        if not user_bot:
            return await event.respond("❌ ইউজার সেশন সক্রিয় নেই! Render-এ USER_SESSION_B64 চেক করুন।")

        match_single = re.search(r"https://t\.me/(?:c/)?([^/]+)/(\d+)", raw)
        if not match_single:
            return await event.respond("❌ সঠিক টেলিগ্রাম লিঙ্ক দিন!")

        raw_channel = match_single.group(1)
        start_id = int(match_single.group(2))
        status = await event.respond("🔍 মিডিয়া খোঁজা হচ্ছে...")

        try:
            target_chat = None
            if raw_channel.isdigit():
                c_id = int(raw_channel)
                possible_ids = [int(f"-100{c_id}"), -c_id, c_id]
                for cid in possible_ids:
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
                return await status.edit("❌ প্রাইভেট চ্যানেল পাওয়া যায়নি! নিশ্চিত করুন আপনার ইউজার অ্যাকাউন্টটি ওই চ্যানেলে জয়েন করা আছে।")

            msg = await user_bot.get_messages(target_chat, ids=start_id)
            if not msg:
                return await status.edit("❌ পোস্টটি খুঁজে পাওয়া যায়নি!")

            msgs_to_dl = [msg]
            if msg.grouped_id:
                nearby = await user_bot.get_messages(target_chat, limit=20, min_id=max(1, start_id - 10), max_id=start_id + 10)
                album = [m for m in nearby if m.grouped_id == msg.grouped_id]
                if album:
                    msgs_to_dl = sorted(album, key=lambda x: x.id)

            has_media = any(m.media or m.file for m in msgs_to_dl)
            if not has_media:
                return await status.edit("❌ এই পোস্টে কোনো ডাউনলোডযোগ্য ফাইল বা ভিডিও নেই!")

            user_thumb = os.path.join(THUMB_DIR, f"{event.sender_id}.jpg")
            thumb_to_use = user_thumb if os.path.exists(user_thumb) else None

            for idx, m in enumerate(msgs_to_dl, 1):
                if m.media or m.file:
                    await status.edit(f"⬇️ ডাউনলোড হচ্ছে ({idx}/{len(msgs_to_dl)})...")
                    st_dl = time.time()
                    fpath = await user_bot.download_media(
                        m,
                        file=DOWNLOAD_DIR,
                        progress_callback=lambda c, t: progress_callback(c, t, event, status, f"⬇️ ডাউনলোড হচ্ছে ({idx}/{len(msgs_to_dl)})", st_dl)
                    )

                    if fpath and os.path.exists(fpath):
                        await status.edit(f"⬆️ আপলোড হচ্ছে ({idx}/{len(msgs_to_dl)})...")
                        st_up = time.time()
                        
                        fsize_mb = os.path.getsize(fpath) / (1024 * 1024)
                        BOT_STATS["downloads"] += 1
                        BOT_STATS["total_mb"] += fsize_mb
                        if event.sender_id not in USER_STATS:
                            USER_STATS[event.sender_id] = {"downloads": 0, "mb": 0.0}
                        USER_STATS[event.sender_id]["downloads"] += 1
                        USER_STATS[event.sender_id]["mb"] += fsize_mb

                        await bot.send_file(
                            event.chat_id,
                            fpath,
                            caption=f"⚡ Downloaded via {CHANNEL_TAG}",
                            thumb=thumb_to_use,
                            force_document=False,
                            progress_callback=lambda c, t: progress_callback(c, t, event, status, f"⬆️ আপলোড হচ্ছে ({idx}/{len(msgs_to_dl)})", st_up)
                        )
                        try:
                            os.remove(fpath)
                        except Exception:
                            pass

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
