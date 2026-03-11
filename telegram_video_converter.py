"""
Telegram Video Auto-Converter Bot Script
=========================================
Yeh script channel ke messages 2-581 tak scan karti hai,
videos @MultiUsage19DC4Bot ko bhejti hai, MP4 convert karti hai,
aur result -1003637459451 mein send karti hai.

Requirements:
    pip install telethon

Usage:
    python telegram_video_converter.py
"""

import asyncio
import random
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaDocument
from telethon.tl.functions.messages import GetHistoryRequest

# ============================================================
#  APNI DETAILS YAHAN BHARO
# ============================================================
import os
API_ID          = int(os.environ.get("API_ID", 0))
API_HASH        = os.environ.get("API_HASH", "")
PHONE           = os.environ.get("PHONE", "")
SESSION_STRING  = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNEL_ID  = -1003356165650   # Source channel ID (t.me/c/3356165650)
BOT_USERNAME       = "@MultiUsage19DC4Bot"
DEST_CHAT_ID       = -1003637459451   # Destination chat

MSG_START    = 2     # Pehla message ID
MSG_END      = 581   # Aakhri message ID
DELAY_MIN    = 3     # Minimum seconds between each video
DELAY_MAX    = 5     # Maximum seconds between each video
# ============================================================

# Session string available ho toh use karo, warna file session
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    client = TelegramClient("session_video_converter", API_ID, API_HASH)


def is_video(message):
    """Check karo ki message mein video hai ya nahi"""
    if message.video:
        return True
    if message.document:
        mime = getattr(message.document, "mime_type", "")
        if mime and mime.startswith("video/"):
            return True
    return False


async def wait_for_bot_response(bot_entity, timeout=120):
    """
    Bot ka response wait karo.
    Bot pehle menu bhejega, phir convert option.
    Returns: last bot message object
    """
    print("   ⏳ Bot ke response ka intezaar hai...")
    await asyncio.sleep(2)  # Bot ko process karne do

    messages = await client.get_messages(bot_entity, limit=5)
    return messages[0] if messages else None


async def click_button_by_text(message, button_text):
    """Message ke buttons mein se text match wala button click karo"""
    if not message or not message.buttons:
        print(f"   ⚠️  Koi button nahi mila message mein")
        return False

    for row in message.buttons:
        for btn in row:
            if button_text.lower() in btn.text.lower():
                print(f"   ✅ Button click kar raha hoon: '{btn.text}'")
                await btn.click()
                return True

    print(f"   ⚠️  '{button_text}' button nahi mila")
    print(f"   Available buttons: {[[b.text for b in row] for row in message.buttons]}")
    return False


async def process_video(message, bot_entity, dest_entity):
    """
    Ek video ko process karo:
    1. Bot ko forward karo
    2. 'Video Converter' button click karo
    3. 'Convert To MP4' button click karo
    4. Converted file destination mein send karo
    """
    msg_id = message.id
    print(f"\n{'='*50}")
    print(f"📹 Processing Message ID: {msg_id}")

    # Step 1: Bot ko seedha forward karo (fast!)
    print(f"   📤 Bot ko forward kar raha hoon...")
    await client.forward_messages(bot_entity, message)
    await asyncio.sleep(2)

    # Step 2: Bot ka pehla response (main menu) lao
    bot_msg = await wait_for_bot_response(bot_entity, timeout=30)
    if not bot_msg:
        print(f"   ❌ Bot ne koi response nahi diya - skip kar raha hoon")
        return False

    # Step 3: 'Video Converter' button dhundo aur click karo
    clicked = await click_button_by_text(bot_msg, "Video Converter")
    if not clicked:
        # Dobara fetch karo
        await asyncio.sleep(3)
        bot_msg = await wait_for_bot_response(bot_entity, timeout=20)
        clicked = await click_button_by_text(bot_msg, "Video Converter")
        if not clicked:
            print(f"   ❌ Video Converter button nahi mila - skip")
            return False

    await asyncio.sleep(2)

    # Step 4: 'Convert To MP4' button dhundo aur click karo
    bot_msg2 = await wait_for_bot_response(bot_entity, timeout=30)
    if not bot_msg2:
        print(f"   ❌ Convert options nahi aaye - skip")
        return False

    clicked2 = await click_button_by_text(bot_msg2, "Convert To MP4")
    if not clicked2:
        print(f"   ❌ Convert To MP4 button nahi mila - skip")
        return False

    print(f"   ⏳ Conversion ka wait kar raha hoon...")

    # Step 5: Converted file ka intezaar (bot processing time)
    await asyncio.sleep(20)  # Bot ko convert karne do

    # Step 6: Bot ka latest message fetch karo (converted file)
    final_messages = await client.get_messages(bot_entity, limit=3)
    converted_msg = None

    for m in final_messages:
        if is_video(m) or (m.document and not m.buttons):
            converted_msg = m
            break

    if not converted_msg:
        # Kuch aur wait karo
        print(f"   ⏳ Thoda aur wait kar raha hoon (file badi ho sakti hai)...")
        await asyncio.sleep(15)
        final_messages = await client.get_messages(bot_entity, limit=3)
        for m in final_messages:
            if is_video(m) or (m.document and not m.buttons):
                converted_msg = m
                break

    if converted_msg:
        print(f"   📨 Converted file destination mein forward kar raha hoon...")
        await client.forward_messages(dest_entity, converted_msg)
        print(f"   ✅ Successfully sent! Message ID: {msg_id}")
        return True
    else:
        print(f"   ❌ Converted file nahi mili - skip kar raha hoon")
        return False


async def main():
    print("🚀 Telegram Video Converter Script Start ho raha hai...")
    print(f"📡 Source: Channel {SOURCE_CHANNEL_ID} (Messages {MSG_START}-{MSG_END})")
    print(f"🤖 Bot: {BOT_USERNAME}")
    print(f"📬 Destination: {DEST_CHAT_ID}")
    print()

    if SESSION_STRING:
        await client.start()
    else:
        await client.start(phone=PHONE)
    print("✅ Telegram mein login ho gaye!\n")

    # Entities resolve karo
    try:
        source_entity = await client.get_entity(SOURCE_CHANNEL_ID)
        bot_entity    = await client.get_entity(BOT_USERNAME)
        dest_entity   = await client.get_entity(DEST_CHAT_ID)
        print(f"✅ Source channel: {getattr(source_entity, 'title', SOURCE_CHANNEL_ID)}")
        print(f"✅ Bot: {BOT_USERNAME}")
        print(f"✅ Destination: {DEST_CHAT_ID}\n")
    except Exception as e:
        print(f"❌ Entity resolve karne mein error: {e}")
        print("Tip: Make sure aap source channel ke member ho aur bot se pehle chat ki ho.")
        return

    # Messages fetch karo (batch mein)
    print(f"📥 Messages fetch kar raha hoon ({MSG_START} se {MSG_END})...")

    video_messages = []
    offset_id = MSG_END + 1
    batch_size = 100

    while True:
        history = await client(GetHistoryRequest(
            peer=source_entity,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=batch_size,
            max_id=0,
            min_id=MSG_START - 1,
            hash=0
        ))

        if not history.messages:
            break

        for msg in history.messages:
            if MSG_START <= msg.id <= MSG_END:
                if is_video(msg):
                    video_messages.append(msg)

        oldest = history.messages[-1].id
        if oldest <= MSG_START:
            break
        offset_id = oldest

    # ID ke order mein sort karo (purane pehle)
    video_messages.sort(key=lambda m: m.id)

    print(f"🎬 Total videos mili: {len(video_messages)}\n")

    if not video_messages:
        print("⚠️  Koi video nahi mili specified range mein!")
        return

    # Har video ko process karo
    success_count = 0
    fail_count = 0

    for i, video_msg in enumerate(video_messages, 1):
        print(f"\n[{i}/{len(video_messages)}] Processing...")

        try:
            result = await process_video(video_msg, bot_entity, dest_entity)
            if result:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"   ❌ Error aaya: {e}")
            fail_count += 1

        # Next video se pehle delay (last video ke baad nahi)
        if i < len(video_messages):
            delay = random.randint(DELAY_MIN, DELAY_MAX)
            print(f"   ⏸️  {delay} seconds wait kar raha hoon...")
            await asyncio.sleep(delay)

    print(f"\n{'='*50}")
    print(f"🏁 Script Complete!")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📊 Total processed: {len(video_messages)}")


if __name__ == "__main__":
    asyncio.run(main())