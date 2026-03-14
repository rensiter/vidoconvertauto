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


async def wait_for_options_reply(last_msg_id: int, timeout: int = 30):
    """Bot ka options wala reply wait karo (inline keyboard wala)"""
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=5):
            if msg.id <= last_msg_id:
                break
            if msg.reply_markup:
                return msg
    return None


async def wait_for_content(last_msg_id: int, timeout: int = 300):
    """Actual content aane tak wait karo, status messages ignore karo"""
    print(f"    ⏳ Download complete hone ka wait kar raha hoon...")
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=10):
            if msg.id <= last_msg_id:
                break
            if msg.text:
                t = msg.text.lower()
                if any(x in t for x in ["downloading", "please wait", "previous task", "processing", "fetching", "your media"]):
                    continue
            if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.sticker:
                print(f"    ✅ Media content mila!")
                return msg
            if msg.text and len(msg.text) > 5:
                print(f"    ✅ Text content mila!")
                return msg
    return None


async def send_to_storage(storage_id, msg, msg_id: int):
    """Content ko storage channel mein copy karo without forwarded tag"""
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
            print(f"[MSG {msg_id}] ⚠️ Unknown content type")
            return False
        print(f"[MSG {msg_id}] ✅ Storage channel mein copy ho gaya!")
        return True
    except Exception as e:
        print(f"[MSG {msg_id}] ❌ Storage send error: {e}")
        return False


async def process_message(msg_id: int, storage_id: int):
    """Ek message ka poora flow"""
    link = f"https://t.me/c/{str(SOURCE_CHANNEL_ID).replace('-100', '')}/{msg_id}"
    print(f"\n[MSG {msg_id}] 🔗 Link: {link}")

    # Step 1: Link bhejo
    last_id = await get_last_bot_msg_id()
    await app.send_message(BOT_USERNAME, link)
    await asyncio.sleep(3)

    # Step 2: Options reply (inline keyboard) wait karo
    options_msg = await wait_for_options_reply(last_id, timeout=30)
    if not options_msg:
        print(f"[MSG {msg_id}] ⚠️ Bot ka options reply nahi aaya, skip")
        return "skipped"

    # Step 3: SIRF button click karo
    last_id = options_msg.id
    print(f"[MSG {msg_id}] 🖱️ 'Without Session' button click kar raha hoon...")
    try:
        await options_msg.click("Without Session")
        print(f"[MSG {msg_id}] ✅ Button clicked!")
    except Exception as e:
        print(f"[MSG {msg_id}] ❌ Button click fail: {e}, skip")
        return "skipped"

    await asyncio.sleep(2)

    # Step 4: Download complete hone tak wait karo
    content = await wait_for_content(last_id, timeout=300)
    if not content:
        print(f"[MSG {msg_id}] ⚠️ Content timeout, skip")
        return "skipped"

    # Step 5: Storage mein bhejo
    success = await send_to_storage(storage_id, content, msg_id)

    # Random 5-10 sec delay
    delay = random.randint(5, 10)
    print(f"[MSG {msg_id}] ⏳ Next ke liye {delay}s wait...")
    await asyncio.sleep(delay)

    return "success" if success else "error"


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
            print(f"✅ Bot resolved: {BOT_USERNAME}")
        except Exception as e:
            print(f"⚠️ Bot resolve error: {e}")

        # Storage channel resolve by username
        try:
            storage_chat = await app.get_chat(STORAGE_USERNAME)
            storage_id = storage_chat.id
            print(f"✅ Storage channel resolved: {storage_chat.title} ({storage_id})")
        except Exception as e:
            print(f"❌ Storage channel resolve fail: {e}")
            return

        # Source channel naam
        try:
            source_chat = await app.get_chat(SOURCE_CHANNEL_ID)
            source_name = source_chat.title or str(SOURCE_CHANNEL_ID)
        except Exception:
            source_name = str(SOURCE_CHANNEL_ID)

        # Start notification
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
                    result = await process_message(msg_id, storage_id)
                    if result == "success":
                        success_count += 1
                    elif result == "skipped":
                        skip_count += 1
                    else:
                        error_count += 1
                    break

                except FloodWait as e:
                    print(f"⏳ FloodWait: {e.value}s wait kar raha hoon...")
                    await asyncio.sleep(e.value + 5)

                except Exception as e:
                    print(f"❌ Unexpected error MSG {msg_id}: {e}")
                    error_count += 1
                    await asyncio.sleep(5)
                    break

        # Summary
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
