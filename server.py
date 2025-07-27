import asyncio
import json
import time
from flask import Flask, request, jsonify
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
import aiohttp

app = Flask(__name__)

# Конфигурация Telegram бота
BOT_TOKEN = "8089270679:AAEfI71LafcY0ube9MpZTgkcKfPVCFa0MCA"
CHAT_ID = "-1002527161177"

# Инициализация aiogram
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список питомцев для уведомлений
PET_LIST = [
    "Corrupted Kitsune", "Raiju", "Kitsune", "Fennec Fox", 
    "Disco Bee", "Raccoon", "Queen Bee", "Dragonfly", 
    "Butterfly", "Mimic Octopus", "T-Rex", "Spinosaurus"
]

# Счетчики для статистики
stats = {
    "total_requests": 0,
    "successful_notifications": 0,
    "failed_notifications": 0,
    "start_time": time.time()
}

# Обработчик команды /kickall
@dp.message(types.Command("kickall"))
async def kickall_command(message: types.Message):
    """Обрабатывает команду /kickall"""
    try:
        # Отправляем подтверждение команды
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🚫 *Команда /kickall получена!*\n\n" +
                 "✅ *Статус:* Команда обрабатывается\n" +
                 "👥 *Действие:* Кик всех игроков со скриптом\n\n" +
                 "⏰ *Время:* " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parse_mode="Markdown"
        )
        
        print(f"✅ Команда /kickall получена от {message.from_user.username}")
        
    except Exception as e:
        print(f"❌ Ошибка обработки команды /kickall: {e}")

async def send_telegram_message(message, parse_mode="Markdown"):
    """Отправляет сообщение в Telegram используя aiogram"""
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        stats["successful_notifications"] += 1
        return True
        
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
        stats["failed_notifications"] += 1
        return False

async def send_telegram_photo(photo_url, caption, parse_mode="Markdown"):
    """Отправляет фото с подписью в Telegram используя aiogram"""
    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo_url,
            caption=caption,
            parse_mode=parse_mode
        )
        stats["successful_notifications"] += 1
        return True
        
    except Exception as e:
        print(f"Ошибка при отправке фото в Telegram: {e}")
        stats["failed_notifications"] += 1
        return False

@app.route('/bot<token>/sendMessage', methods=['POST'])
def send_message(token):
    """Обрабатывает запросы на отправку сообщений"""
    stats["total_requests"] += 1
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Проверяем, что это наш бот
        if token != BOT_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        
        message = data.get("text", "")
        parse_mode = data.get("parse_mode", "Markdown")
        
        # Отправляем в Telegram асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(send_telegram_message(message, parse_mode))
        loop.close()
        
        if success:
            return jsonify({"ok": True, "result": {"message_id": 1}}), 200
        else:
            return jsonify({"ok": False, "error_code": 500}), 500
            
    except Exception as e:
        print(f"Ошибка обработки запроса: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/bot<token>/sendPhoto', methods=['POST'])
def send_photo(token):
    """Обрабатывает запросы на отправку фото"""
    stats["total_requests"] += 1
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Проверяем, что это наш бот
        if token != BOT_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        
        photo_url = data.get("photo", "")
        caption = data.get("caption", "")
        parse_mode = data.get("parse_mode", "Markdown")
        
        # Отправляем в Telegram асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(send_telegram_photo(photo_url, caption, parse_mode))
        loop.close()
        
        if success:
            return jsonify({"ok": True, "result": {"message_id": 1}}), 200
        else:
            return jsonify({"ok": False, "error_code": 500}), 500
            
    except Exception as e:
        print(f"Ошибка обработки запроса фото: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/bot<token>/getUpdates', methods=['GET'])
def get_updates(token):
    """Обрабатывает запросы на получение обновлений"""
    stats["total_requests"] += 1
    
    try:
        # Проверяем, что это наш бот
        if token != BOT_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        
        offset = request.args.get('offset', 0)
        
        # Получаем обновления от Telegram используя aiogram
        async def get_updates_async():
            try:
                updates = await bot.get_updates(offset=int(offset))
                return {"ok": True, "result": [update.model_dump() for update in updates]}
            except Exception as e:
                return {"ok": False, "error_code": 500, "description": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_updates_async())
        loop.close()
        
        return jsonify(result), 200 if result["ok"] else 500
            
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Возвращает статистику сервера"""
    uptime = time.time() - stats["start_time"]
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    
    return jsonify({
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "total_requests": stats["total_requests"],
        "successful_notifications": stats["successful_notifications"],
        "failed_notifications": stats["failed_notifications"],
        "success_rate": f"{(stats['successful_notifications'] / max(stats['total_requests'], 1) * 100):.1f}%"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервера"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def home():
    """Главная страница"""
    return jsonify({
        "message": "Telegram Proxy Server",
        "version": "1.0",
        "endpoints": {
            "send_message": "/bot<token>/sendMessage",
            "send_photo": "/bot<token>/sendPhoto", 
            "get_updates": "/bot<token>/getUpdates",
            "stats": "/stats",
            "health": "/health"
        }
    })

if __name__ == '__main__':
    print("🚀 Telegram Proxy Server с aiogram запущен!")
    print(f"📡 Сервер слушает на порту 9999")
    print(f"🤖 Бот токен: {BOT_TOKEN[:20]}...")
    print(f"💬 Чат ID: {CHAT_ID}")
    print(f"🐾 Список питомцев: {len(PET_LIST)} питомцев")
    print("=" * 50)
    
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=9999, debug=False) 
