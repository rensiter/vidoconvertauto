import asyncio
import os
import random
from pyrogram import Client
from pyrogram.errors import FloodWait

# ============ VARIABLES ============
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
SOURCE_CHANNEL_ID = -1002533036931
BOT_USERNAME = "@MultiUsage19DC4Bot"
STORAGE_USERNAME = "@miningtohole"
# ===================================

MSG_START = 3
MSG_END = 119

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


async def get_last_bot_msg_id():
    async for msg in app.get_chat_history(BOT_USERNAME, limit=1):
        return msg.id
    return 0


async def wait_for_button_msg(after_id: int, timeout: int = 30):
    """Bot ka inline button wala message wait karo"""
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=5):
            if msg.id <= after_id:
                break
            # Busy message — /cancel bhejo
            if msg.text and "previous task" in msg.text.lower():
                return "busy"
            # Inline buttons wala message mila
            if msg.reply_markup:
                return msg
    return None


async def wait_for_final_content(after_id: int, timeout: int = 300):
    """
    Bot ka final content wait karo.
    'Downloading' / 'Progress' wale messages ignore karo.
    Sirf actual media ya text return karo.
    """
    print(f"    ⏳ Bot se content ka wait kar raha hoon...")
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=10):
            if msg.id <= after_id:
                break

            # Ye sab ignore karo — ye status messages hain
            if msg.text:
                t = msg.text.lower()
                skip_words = ["downloading", "please wait", "previous task",
                              "processing", "fetching", "your media file is",
                              "progress", "cancel"]
                if any(x in t for x in skip_words):
                    continue

            # Inline buttons wala message bhi skip karo
            if msg.reply_markup:
                continue

            # ✅ Actual content mila!
            if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.sticker:
                print(f"    ✅ Media content mila!")
                return msg
            if msg.text and len(msg.text) > 3:
                print(f"    ✅ Text content mila!")
                return msg

    return None


async def send_to_storage(storage_id: int, msg, msg_id: int):
    """Content storage channel mein bhejo — without forwarded tag"""
    try:
        caption = msg.caption or ""
        if msg.photo:
            await app.send_photo(storage_id, msg.photo.file_id, caption=caption)
        elif msg.video:
            await app.send_video(storage_id, msg.video.file_id, caption=caption)
        elif msg.document:
            await app.send_document(storage_id, msg.document.file_id, caption=caption)
        elif msg.audio:
            await app.send_audio(storage_id, msg.audio.file_id, caption=caption)
        elif msg.voice:
            await app.send_voice(storage_id, msg.voice.file_id, caption=caption)
        elif msg.sticker:
            await app.send_sticker(storage_id, msg.sticker.file_id)
        elif msg.text:
            await app.send_message(storage_id, msg.text)
        else:
            print(f"[MSG {msg_id}] ⚠️ Unknown content type, skip")
            return False
        print(f"[MSG {msg_id}] ✅ Storage mein bhej diya!")
        return True
    except Exception as e:
        print(f"[MSG {msg_id}] ❌ Storage error: {e}")
        return False


async def process_one(msg_id: int, storage_id: int):
    """Ek message ka full flow"""
    link = f"https://t.me/c/{str(SOURCE_CHANNEL_ID).replace('-100', '')}/{msg_id}"
    print(f"\n[MSG {msg_id}] 🔗 Link bhej raha hoon...")

    for attempt in range(3):
        # Step 1: Link bhejo
        last_id = await get_last_bot_msg_id()
        await app.send_message(BOT_USERNAME, link)
        await asyncio.sleep(3)

        # Step 2: Button wala message wait karo
        btn_msg = await wait_for_button_msg(last_id, timeout=30)

        if btn_msg == "busy":
            print(f"[MSG {msg_id}] ⚠️ Bot busy hai, /cancel bhej ke retry ({attempt+1}/3)...")
            await app.send_message(BOT_USERNAME, "/cancel")
            await asyncio.sleep(4)
            continue

        if not btn_msg:
            print(f"[MSG {msg_id}] ⚠️ Button message nahi aaya, skip")
            return "skipped"

        # Step 3: "Without Session" button click karo
        after_btn_id = btn_msg.id
        print(f"[MSG {msg_id}] 🖱️ 'Without Session' click kar raha hoon...")
        try:
            await btn_msg.click("Without Session")
            print(f"[MSG {msg_id}] ✅ Clicked!")
        except Exception as e:
            print(f"[MSG {msg_id}] ❌ Click fail: {e}")
            return "skipped"

        await asyncio.sleep(2)

        # Step 4: Bot ka final content wait karo (download hone do)
        content = await wait_for_final_content(after_btn_id, timeout=300)

        if not content:
            print(f"[MSG {msg_id}] ⚠️ Content nahi aaya, skip")
            return "skipped"

        # Step 5: Storage mein bhejo
        ok = await send_to_storage(storage_id, content, msg_id)

        # Step 6: 6-12 sec wait karo
        delay = random.randint(6, 12)
        print(f"[MSG {msg_id}] ⏳ {delay}s wait kar raha hoon next ke liye...")
        await asyncio.sleep(delay)

        return "success" if ok else "error"

    return "skipped"


async def main():
    import datetime

    print("🚀 Script start ho rahi hai...")
    print(f"📋 Range: MSG {MSG_START} to {MSG_END}")
    print(f"🤖 Bot: {BOT_USERNAME}")

    success_count = 0
    skip_count = 0
    error_count = 0
    start_time = datetime.datetime.now()

    async with app:
        # Bot resolve
        try:
            await app.get_chat(BOT_USERNAME)
            print(f"✅ Bot resolved")
        except Exception as e:
            print(f"⚠️ Bot resolve error: {e}")

        # Storage channel resolve
        try:
            storage_chat = await app.get_chat(STORAGE_USERNAME)
            storage_id = storage_chat.id
            print(f"✅ Storage: {storage_chat.title}")
        except Exception as e:
            print(f"❌ Storage resolve fail: {e}")
            return

        # Source channel naam
        source_name = str(SOURCE_CHANNEL_ID)
        try:
            source_chat = await app.get_chat(SOURCE_CHANNEL_ID)
            source_name = source_chat.title or source_name
            print(f"✅ Source: {source_name}")
        except Exception:
            print(f"⚠️ Source naam nahi mila, ID use karunga")

        # Start message
        await app.send_message(
            storage_id,
            f"🚀 **Task Started!**\n\n"
            f"📢 **Source:** {source_name}\n"
            f"📋 **Range:** MSG {MSG_START} to {MSG_END}\n"
            f"🕐 **Start:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⏳ Processing..."
        )

        # Main loop
        for msg_id in range(MSG_START, MSG_END + 1):
            while True:
                try:
                    result = await process_one(msg_id, storage_id)
                    if result == "success":
                        success_count += 1
                    elif result == "skipped":
                        skip_count += 1
                    else:
                        error_count += 1
                    break

                except FloodWait as e:
                    print(f"⏳ FloodWait: {e.value}s...")
                    await asyncio.sleep(e.value + 5)

                except Exception as e:
                    print(f"❌ Error MSG {msg_id}: {e}")
                    error_count += 1
                    await asyncio.sleep(5)
                    break

        # Final summary
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        h, rem = divmod(int(duration.total_seconds()), 3600)
        m, s = divmod(rem, 60)

        summary = (
            f"✅ **Task Complete!**\n\n"
            f"📢 **Source:** {source_name}\n"
            f"📋 **Range:** MSG {MSG_START} to {MSG_END}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✅ **Successful:** {success_count}\n"
            f"⏭️ **Skipped:** {skip_count}\n"
            f"❌ **Errors:** {error_count}\n"
            f"📦 **Total:** {success_count + skip_count + error_count}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🕐 **Start:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🕑 **End:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⏱️ **Duration:** {h}h {m}m {s}s"
        )

        await app.send_message(storage_id, summary)
        print("\n" + summary)


if __name__ == "__main__":
    asyncio.run(main())
