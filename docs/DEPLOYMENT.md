# Запуск проекта

## Требования

- Python 3.10+
- Git

## Установка

1. Клонируй репозиторий
   git clone https://github.com/baravko/baravko.git
   cd baravko

2. Создай виртуальное окружение
   python -m venv venv

3. Активируй окружение
   - Windows: venv\Scripts\activate
   - Mac/Linux: source venv/bin/activate

4. Установи зависимости
   pip install flask sqlalchemy werkzeug requests

5. Запусти приложение
   python app/main.py

6. Открой в браузере
   http://127.0.0.1:5000