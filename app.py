# Vercel требует файл app.py
# Импортируем все из server.py
from server import app

# Экспортируем приложение для Vercel
if __name__ == '__main__':
    app.run() 