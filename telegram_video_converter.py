import asyncio
import os
import random
import datetime
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

# ============ VARIABLES (Railway Environment Se Ayenge) ============
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNEL_ID = -1002533036931
BOT_USERNAME = "@MultiUsage19DC4Bot"
STORAGE_CHANNEL_ID = -1003637459451 # Direct ID use karna best hai Railway pe

MSG_START = 3
MSG_END = 119
# ===================================================================

app = Client(
    "my_account", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    session_string=SESSION_STRING,
    in_memory=True # Railway pe session file error se bachne ke liye
)

async def get_last_bot_msg_id():
    async for msg in app.get_chat_history(BOT_USERNAME, limit=1):
        return msg.id
    return 0

async def wait_for_final_content(after_id: int, timeout: int = 300):
    """Bot ka final content wait karo. Status messages ignore karo."""
    for _ in range(timeout):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(BOT_USERNAME, limit=5):
            if msg.id <= after_id:
                break

            # Skip common status keywords
            if msg.text:
                t = msg.text.lower()
                skip_words = ["downloading", "please wait", "processing", "fetching", "progress", "cancel", "searching"]
                if any(x in t for x in skip_words):
                    continue
                
                # Agar bot 'Without Session' ka button maange
                if msg.reply_markup:
                    for row in msg.reply_markup.inline_keyboard:
                        for btn in row:
                            if "Without Session" in btn.text:
                                try:
                                    await msg.click(btn.text)
                                    print("   🖱️ 'Without Session' clicked automatically.")
                                    await asyncio.sleep(2)
                                except: pass
                    continue

            # Check for actual content
            if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.sticker or (msg.text and len(msg.text) > 5):
                return msg
    return None

async def process_one(msg_id: int):
    # Link formation (Private channel link format)
    clean_id = str(SOURCE_CHANNEL_ID).replace("-100", "")
    link = f"https://t.me/c/{clean_id}/{msg_id}"
    
    print(f"\n[MSG {msg_id}] 🔗 Processing Link...")
    
    last_id = await get_last_bot_msg_id()
    await app.send_message(BOT_USERNAME, link)
    
    # Wait for response
    content = await wait_for_final_content(last_id)
    
    if content:
        # Forward or Copy to storage (Copying is better to avoid 'forwarded' tag)
        await content.copy(STORAGE_CHANNEL_ID)
        print(f"[MSG {msg_id}] ✅ Storage mein save ho gaya!")
        return "success"
    else:
        print(f"[MSG {msg_id}] ⚠️ Content nahi mila ya timeout.")
        return "skipped"

async def main():
    print("🚀 Script starting for Railway deployment...")
    
    async with app:
        start_time = datetime.datetime.now()
        success_count = 0
        
        # Start Notification
        await app.send_message(STORAGE_CHANNEL_ID, f"🚀 **Automation Started**\nRange: `{MSG_START}` to `{MSG_END}`")

        for msg_id in range(MSG_START, MSG_END + 1):
            try:
                result = await process_one(msg_id)
                if result == "success":
                    success_count += 1
                
                # User ki demand ke mutabiq 6-12 sec wait
                wait_time = random.randint(6, 12)
                print(f"⏳ Sleeping for {wait_time}s...")
                await asyncio.sleep(wait_time)

            except FloodWait as e:
                print(f"🛑 FloodWait: Waiting {e.value}s")
                await asyncio.sleep(e.value + 5)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

        # Final Summary
        summary = f"✅ **Task Completed!**\nTotal Saved: `{success_count}`\nDuration: `{datetime.datetime.now() - start_time}`"
        await app.send_message(STORAGE_CHANNEL_ID, summary)
        print(summary)

if __name__ == "__main__":
    app.run(main())
