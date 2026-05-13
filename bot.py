import logging
import json
import os
import asyncio
from telegram import Update
from telegram.ext import Application, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8714350872:AAEYtlzuOSe-xU6zKj0hwv02Iu6KIp80qg8"
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "auto_message" in data and "auto_messages" not in data:
                data["auto_messages"] = [data["auto_message"]]
                del data["auto_message"]
            return data
    return {"owner_id": None, "auto_messages": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

bot_data = load_data()

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    join_request = update.chat_join_request
    user = join_request.from_user
    
    try:
        messages = bot_data.get("auto_messages", [])
        if not messages:
            return
            
        for msg in messages:
            try:
                if isinstance(msg, str):
                    # अगर पुराना टेक्स्ट है
                    await context.bot.send_message(chat_id=user.id, text=msg)
                else:
                    # नया सिस्टम: कॉपी मैसेज (Video, Voice, APK, Photo सब कुछ सपोर्ट करेगा)
                    await context.bot.copy_message(
                        chat_id=user.id, 
                        from_chat_id=msg["chat_id"], 
                        message_id=msg["message_id"]
                    )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to send a message part: {e}")
                
    except Exception as e:
        logger.error(f"Error handling join request: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    if bot_data["owner_id"] is None:
        bot_data["owner_id"] = user.id
        save_data(bot_data)
        await update.message.reply_text(
            f"🎉 बधाई हो {user.first_name}! अब आप इस बोट के Owner हैं।\n\n"
            "अब आप **Video, Voice Note, APK File या Text** कुछ भी सेट कर सकते हैं!\n\n"
            "**मैसेज कैसे ऐड करें?**\n"
            "1. इस चैट में कोई भी वीडियो, फाइल या मैसेज भेजें।\n"
            "2. उस मैसेज को **Reply** करें और रिप्लाई में `/add` लिखकर भेज दें।\n\n"
            "अन्य कमांड्स:\n"
            "`/viewmessages` - सारे सेट किये हुए मैसेज देखने के लिए\n"
            "`/clearmessages` - पुराने सारे मैसेज डिलीट करने के लिए"
        )
    elif bot_data["owner_id"] == user.id:
        await update.message.reply_text(
            "हेलो बॉस! कोई भी Video, Voice, File या Text ऐड करने के लिए:\n\n"
            "1. पहले उसे यहाँ सेंड करें।\n"
            "2. फिर उस मैसेज को **Reply** करके `/add` कमांड भेजें।\n\n"
            "अन्य कमांड्स:\n"
            "`/viewmessages` - सारे मैसेज देखें\n"
            "`/clearmessages` - सारे मैसेज डिलीट करें"
        )
    else:
        await update.message.reply_text("सॉरी, आप इस बोट के Owner नहीं हैं।")

async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if bot_data["owner_id"] != user.id:
        return
        
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ आपको इस कमांड को किसी मैसेज के **Reply** में भेजना होगा!\n\n"
            "जिस वीडियो, फाइल या टेक्स्ट को आप ऐड करना चाहते हैं, उसे स्वाइप करके Reply करें और फिर `/add` लिखें।"
        )
        return
        
    target_msg = update.message.reply_to_message
    
    if "auto_messages" not in bot_data:
        bot_data["auto_messages"] = []
        
    # हम मैसेज का ID सेव कर रहे हैं, जिससे वीडियो/फाइल भी सेव हो जाएगी!
    new_item = {
        "chat_id": target_msg.chat_id,
        "message_id": target_msg.message_id
    }
    
    bot_data["auto_messages"].append(new_item)
    save_data(bot_data)
    
    count = len(bot_data["auto_messages"])
    await update.message.reply_text(f"✅ शानदार! यह (Video/Voice/File/Text) सक्सेसफुली मैसेज #{count} के रूप में ऐड हो गया है।")

async def view_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if bot_data["owner_id"] != user.id:
        return
        
    messages = bot_data.get("auto_messages", [])
    if not messages:
        await update.message.reply_text("अभी कोई भी मैसेज सेट नहीं है।")
        return
        
    await update.message.reply_text(f"अभी कुल {len(messages)} मैसेज सेट हैं। मैं आपको वो सभी मैसेज एक-एक करके भेज रहा हूँ:")
    
    for i, msg in enumerate(messages, 1):
        await update.message.reply_text(f"👇 **मैसेज {i}** 👇")
        if isinstance(msg, str):
            await context.bot.send_message(chat_id=user.id, text=msg)
        else:
            await context.bot.copy_message(
                chat_id=user.id, 
                from_chat_id=msg["chat_id"], 
                message_id=msg["message_id"]
            )
        await asyncio.sleep(0.5)
        
    await update.message.reply_text("👆 ये सारे मैसेज यूज़र्स को इसी क्रम (order) में भेजे जाएंगे।")

async def clear_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if bot_data["owner_id"] != user.id:
        return
        
    bot_data["auto_messages"] = []
    save_data(bot_data)
    await update.message.reply_text("🗑️ पुरानी सारी लिस्ट क्लियर कर दी गई है!\n\nअब आप नए सिरे से Video/Voice/APK भेजकर और उसे Reply करके `/add` कर सकते हैं।")

async def general_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if bot_data["owner_id"] == user.id:
        if update.message.text and update.message.text.startswith('/'):
            return 
        await update.message.reply_text("⬆️ अगर आप इस वीडियो/फाइल/मैसेज को यूज़र्स को भेजना चाहते हैं, तो इस मैसेज को **Reply** करें और लिखें:\n`/add`")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(ChatJoinRequestHandler(handle_join_request))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("add", add_reply_command))
    application.add_handler(CommandHandler("viewmessages", view_messages_command))
    application.add_handler(CommandHandler("clearmessages", clear_messages_command))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, general_message_handler))
    
    print("Super Advanced Bot is running... Waiting for commands.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
