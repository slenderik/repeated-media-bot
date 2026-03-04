import asyncio
import os
import sqlite3
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ContentType

# -------------------- LOGGING --------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# -------------------- ENV --------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# -------------------- BOT --------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -------------------- DATABASE --------------------

DB_PATH = os.getenv("DB_PATH", "media.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_unique_id TEXT NOT NULL,
    message_link TEXT NOT NULL
)
""")
conn.commit()

logger.info(f"📂 База данных подключена: {DB_PATH}")

def save_media(file_unique_id: str, message_link: str):
    logger.info(f"💾 Сохраняем в БД: {file_unique_id}")
    cursor.execute(
        "INSERT INTO media (file_unique_id, message_link) VALUES (?, ?)",
        (file_unique_id, message_link)
    )
    conn.commit()


def get_existing_media(file_unique_id: str):
    logger.info(f"🔎 Проверяем в БД: {file_unique_id}")
    cursor.execute(
        "SELECT message_link FROM media WHERE file_unique_id = ?",
        (file_unique_id,)
    )
    result = cursor.fetchall()
    logger.info(f"📊 Найдено совпадений: {len(result)}")
    return result


# -------------------- HANDLER --------------------

@dp.message(F.chat.id == GROUP_ID)
async def check_media(message: Message):

    logger.info(
        f"👀 Новое сообщение | "
        f"user_id={message.from_user.id if message.from_user else 'unknown'} | "
        f"message_id={message.message_id} | "
        f"type={message.content_type}"
    )

    file_unique_id = None

    # Фото
    if message.content_type == ContentType.PHOTO:
        file_unique_id = message.photo[-1].file_unique_id
        logger.info("🖼 Обнаружено фото")

    # Видео
    elif message.content_type == ContentType.VIDEO:
        file_unique_id = message.video.file_unique_id
        logger.info("🎬 Обнаружено видео")

    if not file_unique_id:
        logger.info("❌ Медиа нет — пропускаем")
        return

    # Формируем ссылку
    if message.chat.username:
        message_link = f"https://t.me/{message.chat.username}/{message.message_id}"
    else:
        chat_id = str(message.chat.id).replace("-100", "")
        message_link = f"https://t.me/c/{chat_id}/{message.message_id}"

    existing = get_existing_media(file_unique_id)

    if existing:
        logger.warning("⚠️ Найден дубликат!")

        links = "\n".join([row[0] for row in existing])
        await message.reply(
            f"⚠️ Это медиа уже отправляли!\n\nВот все совпадения:\n{links}",
            disable_web_page_preview=True
        )
    else:
        logger.info("✅ Дубликатов нет")

    save_media(file_unique_id, message_link)


# -------------------- START --------------------

async def main():
    logger.info("🚀 Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())