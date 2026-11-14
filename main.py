
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Missing API keys in environment variables")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"

conversations = {}

SYSTEM_PROMPT = """
تو دستیار هوشمند رسمی آرتیوند هستی.
نام تو Artivand AI است.

زبان اصلی پاسخ‌گویی تو فارسی است.
با لحنی حرفه‌ای، صمیمی، دقیق و صادقانه صحبت کن.
در موضوعات اقتصادی و تجاری واقع‌بین باش.
اطلاعات و اعداد نامطمئن را به عنوان واقعیت بیان نکن.
به پرسش‌های کاربران پاسخ مفید و روشن بده.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\n"
        "به دستیار هوشمند آرتیوند خوش آمدی.\n\n"
        "من Artivand AI هستم.\n"
        "هر سؤالی داری بپرس تا کمکت کنم.\n\n"
        "برای شروع مجدد مکالمه دستور /reset را بفرست."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversations.pop(user_id, None)
    await update.message.reply_text("حافظه مکالمه فعلی پاک شد. آماده‌ام! 🤖")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    history = conversations.get(user_id, [])

    history.append({
        "role": "user",
        "content": user_text
    })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history[-12:]

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1200
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "پاسخی دریافت نشد. لطفاً دوباره تلاش کن."

        history.append({
            "role": "assistant",
            "content": answer
        })

        conversations[user_id] = history[-20:]

        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])

    except Exception:
        logging.exception("AI request failed")
        await update.message.reply_text(
            "در حال حاضر ارتباط با هوش مصنوعی برقرار نشد. "
            "لطفاً کمی بعد دوباره تلاش کن."
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    logging.info("Artivand AI is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()

