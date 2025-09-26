import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_TOKEN")  # на Render будем добавлять эту переменную окружения

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# простые клавиатуры
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 Текст")
    kb.row("🎭 РП", "🧩 Игры", "📐 Задачи")
    kb.row("🎨 Генерация")
    kb.row("📂 Работа с файлами")
    kb.row("📖 История")
    return kb

back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_kb.add("🔙 Назад")

# подменю-примеры
rp_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
rp_kb.row("▶️ Начать новый RP", "⏩ Продолжить RP")
rp_kb.add("🔙 Назад")

tasks_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
tasks_kb.row("✏️ Ввести текст задачи", "📄 Загрузить файл")
tasks_kb.row("📷 Загрузить фото задачи")
tasks_kb.add("🔙 Назад")

gen_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
gen_kb.row("🖼 Изображение", "🗂 Стикер")
gen_kb.row("🎬 Видео", "⭕ Кружочки")
gen_kb.row("🗣 Аудио")
gen_kb.add("🔙 Назад")

files_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
files_kb.row("📁 Создать файл", "👀 Просмотр файла")
files_kb.row("🔍 Анализ изображения")
files_kb.add("🔙 Назад")

games_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
games_kb.row("❓ Викторины", "🧩 Логические задачи")
games_kb.row("🕵️‍♂️ Угадай персонажа", "🎲 Случайные мини-игры")
games_kb.add("🔙 Назад")

history_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
history_kb.row("📜 Просмотр RP-сцен", "📜 Просмотр задач")
history_kb.row("📜 Просмотр генераций")
history_kb.add("🔙 Назад")

# простой in-memory контекст (пока для теста)
USER_CTX = {}  # {chat_id: {"menu": "text"/"rp"/..., "data": {...}}}

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    USER_CTX.pop(message.chat.id, None)
    await message.answer("Привет! Я Лира — NovaAI. Выбирай пункт меню.", reply_markup=main_kb())

@dp.message_handler(lambda m: m.text == "🔙 Назад")
async def handle_back(message: types.Message):
    cid = message.chat.id
    # если пользователь был в Тексте — очищаем контекст Текста
    ctx = USER_CTX.get(cid, {})
    if ctx.get("menu") == "text":
        # удаляем историю текст-сессии
        ctx.pop("text_history", None)
    # сохраняем контент (для всех остальных разделов мы сохраняем в ctx)
    USER_CTX[cid] = {"menu": None, "data": ctx.get("data", {})}
    await message.answer("Возврат в главное меню.", reply_markup=main_kb())

@dp.message_handler(lambda m: m.text == "📝 Текст")
async def enter_text(message: types.Message):
    cid = message.chat.id
    USER_CTX[cid] = {"menu": "text", "text_history": []}
    await message.answer("Вошёл в раздел Текст. Пиши — я буду отвечать (это чистая сессия). Нажми 'Назад' чтобы выйти.", reply_markup=back_kb)

@dp.message_handler(lambda m: m.text == "🎭 РП")
async def enter_rp(message: types.Message):
    cid = message.chat.id
    ctx = USER_CTX.get(cid, {})
    # если уже была RP-сессия — восстановим
    USER_CTX[cid] = ctx
    USER_CTX[cid].setdefault("menu", "rp")
    USER_CTX[cid].setdefault("rp_history", [])
    await message.answer("Раздел RP. Выбери: Начать новый RP или Продолжить.", reply_markup=rp_kb)

@dp.message_handler(lambda m: m.text == "🧩 Игры")
async def enter_games(message: types.Message):
    cid = message.chat.id
    USER_CTX.setdefault(cid, {})["menu"] = "games"
    await message.answer("Раздел Игры. Выбери тип игры.", reply_markup=games_kb)

@dp.message_handler(lambda m: m.text == "📐 Задачи")
async def enter_tasks(message: types.Message):
    cid = message.chat.id
    USER_CTX.setdefault(cid, {})["menu"] = "tasks"
    USER_CTX[cid].setdefault("tasks_history", [])
    await message.answer("Раздел Задачи. Отправь текст, файл или фото задачи.", reply_markup=tasks_kb)

@dp.message_handler(lambda m: m.text == "🎨 Генерация")
async def enter_gen(message: types.Message):
    cid = message.chat.id
    USER_CTX.setdefault(cid, {})["menu"] = "generation"
    USER_CTX[cid].setdefault("gen_history", [])
    await message.answer("Раздел Генерация. Выбери что создать.", reply_markup=gen_kb)

@dp.message_handler(lambda m: m.text == "📂 Работа с файлами")
async def enter_files(message: types.Message):
    cid = message.chat.id
    USER_CTX.setdefault(cid, {})["menu"] = "files"
    await message.answer("Раздел Работа с файлами.", reply_markup=files_kb)

@dp.message_handler(lambda m: m.text == "📖 История")
async def enter_history(message: types.Message):
    cid = message.chat.id
    USER_CTX.setdefault(cid, {})["menu"] = "history"
    await message.answer("Раздел История.", reply_markup=history_kb)

# общий обработчик текстовых сообщений
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def message_router(message: types.Message):
    cid = message.chat.id
    text = message.text.strip()
    ctx = USER_CTX.get(cid, {"menu": None})
    menu = ctx.get("menu")

    if menu == "text":
        # простая заглушка: эхо + сохраняем в сессию
        ctx.setdefault("text_history", []).append({"user": text})
        reply = f"Лира (заглушка): я получила: {text}"
        ctx.setdefault("text_history", []).append({"bot": reply})
        await message.answer(reply)
        return

    if menu == "rp":
        ctx.setdefault("rp_history", []).append({"user": text})
        await message.answer("RP: запомнил. (Заглушка).")
        return

    if menu == "tasks":
        ctx.setdefault("tasks_history", []).append({"user": text})
        await message.answer("Задача принята. Я попробую решить (заглушка).")
        return

    if menu == "generation":
        ctx.setdefault("gen_history", []).append({"user": text})
        await message.answer("Генерация: получил запрос. (заглушка)")
        return

    if menu == "files":
        await message.answer("Работа с файлами: команда принята. (заглушка)")
        return

    if menu == "games":
        await message.answer("Игры: выбери режим в меню. (заглушка)")
        return

    # если меню не выбран — показываем главное меню
    await message.answer("Нажми кнопку меню ниже.", reply_markup=main_kb())

@dp.message_handler(content_types=[types.ContentType.DOCUMENT, types.ContentType.PHOTO])
async def handle_files(message: types.Message):
    cid = message.chat.id
    ctx = USER_CTX.setdefault(cid, {"menu": None})
    menu = ctx.get("menu")
    if menu == "tasks":
        await message.answer("Файл/фото получено для задачи. (Заглушка — дальше будет OCR/решение)")
        return
    if menu == "files":
        await message.answer("Файл принят (Работа с файлами).")
        return
    await message.answer("Файл/фото получено, но пока не настроено действие для этого раздела.")

if __name__ == "__main__":
    print("Bot started (local).")
    executor.start_polling(dp, skip_updates=True)
