import asyncio
import os
from pyrogram import Client
from pyrogram.errors import FloodWait, MessageNotModified

# ============ VARIABLES (Railway mein set karo) ============
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SOURCE_CHANNEL_ID = int(os.environ.get("SOURCE_CHANNEL_ID", "0"))  # e.g. -1002533036931
STORAGE_CHANNEL_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "0"))  # e.g. -1001234567890
BOT_USERNAME = "@MultiUsage19DC4Bot"
# ==========================================================

MSG_START = 3
MSG_END = 119

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)


async def wait_for_bot_reply(last_msg_id: int, timeout: int = 60):
    """Bot ka reply aane tak wait karo"""
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=5):
            if msg.id > last_msg_id and msg.from_user and msg.from_user.is_bot:
                return msg
    return None


async def get_last_bot_msg_id():
    """Bot chat ka last message ID lo"""
    async for msg in app.get_chat_history(BOT_USERNAME, limit=1):
        return msg.id
    return 0


async def send_link_and_handle(msg_id: int):
    """Ek message ID ke liye poora flow chalao"""
    link = f"https://t.me/c/{str(SOURCE_CHANNEL_ID).replace('-100', '')}/{msg_id}"
    print(f"\n[MSG {msg_id}] Link bhej raha hoon: {link}")

    # Step 1: Bot ko link bhejo
    last_id = await get_last_bot_msg_id()
    await app.send_message(BOT_USERNAME, link)
    await asyncio.sleep(2)

    # Step 2: Bot ka pehla reply wait karo (options wala message)
    reply = await wait_for_bot_reply(last_id, timeout=30)
    if not reply:
        print(f"[MSG {msg_id}] Bot ne reply nahi kiya, skip kar raha hoon")
        return

    print(f"[MSG {msg_id}] Bot ka reply mila, 'Without Session' bhej raha hoon")

    # Step 3: "Without Session" button ka command bhejo
    last_id = reply.id
    await app.send_message(BOT_USERNAME, "Without Session")
    await asyncio.sleep(2)

    # Step 4: Bot ka content reply wait karo (media/text)
    content_reply = await wait_for_bot_reply(last_id, timeout=90)
    if not content_reply:
        print(f"[MSG {msg_id}] Content nahi mila, skip")
        return

    print(f"[MSG {msg_id}] Content mila! Storage channel mein copy kar raha hoon...")

    # Step 5: Content ko storage channel mein copy karo (without forwarded tag)
    try:
        if content_reply.text:
            await app.send_message(STORAGE_CHANNEL_ID, content_reply.text)

        elif content_reply.photo:
            await app.send_photo(
                STORAGE_CHANNEL_ID,
                content_reply.photo.file_id,
                caption=content_reply.caption or ""
            )

        elif content_reply.video:
            await app.send_video(
                STORAGE_CHANNEL_ID,
                content_reply.video.file_id,
                caption=content_reply.caption or ""
            )

        elif content_reply.document:
            await app.send_document(
                STORAGE_CHANNEL_ID,
                content_reply.document.file_id,
                caption=content_reply.caption or ""
            )

        elif content_reply.audio:
            await app.send_audio(
                STORAGE_CHANNEL_ID,
                content_reply.audio.file_id,
                caption=content_reply.caption or ""
            )

        elif content_reply.voice:
            await app.send_voice(
                STORAGE_CHANNEL_ID,
                content_reply.voice.file_id,
                caption=content_reply.caption or ""
            )

        elif content_reply.sticker:
            await app.send_sticker(
                STORAGE_CHANNEL_ID,
                content_reply.sticker.file_id
            )

        print(f"[MSG {msg_id}] ✅ Successfully copied to storage channel!")

    except Exception as e:
        print(f"[MSG {msg_id}] ❌ Copy karne mein error: {e}")


async def main():
    print("🚀 Script start ho rahi hai...")
    print(f"📋 Range: MSG {MSG_START} to {MSG_END}")
    print(f"🤖 Bot: {BOT_USERNAME}")

    async with app:
        for msg_id in range(MSG_START, MSG_END + 1):
            while True:
                try:
                    await send_link_and_handle(msg_id)
                    await asyncio.sleep(3)  # Next message se pehle thoda wait
                    break

                except FloodWait as e:
                    print(f"⏳ FloodWait: {e.value} seconds wait kar raha hoon...")
                    await asyncio.sleep(e.value + 5)
                    # Auto resume same msg_id se

                except Exception as e:
                    print(f"❌ Error MSG {msg_id}: {e}")
                    await asyncio.sleep(5)
                    break

    print("\n✅ Sab complete ho gaya!")


if __name__ == "__main__":
    asyncio.run(main())
