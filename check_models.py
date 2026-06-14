import os
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Берём ключ из переменной окружения
KEY = os.getenv("OPENROUTER_API_KEY")

if not KEY:
    print("ОШИБКА: Не найден OPENROUTER_API_KEY в .env файле")
    print("Создай файл .env и добавь туда строку:")
    print("OPENROUTER_API_KEY=sk-or-...")
    exit(1)


def get_free_models():
    """Получает список бесплатных моделей с OpenRouter"""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {KEY}"},
            timeout=10
        )
        data = resp.json()

        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and "data" in data:
            models = data["data"]
        else:
            return []

        free_models = []
        for m in models:
            if isinstance(m, dict):
                pricing = m.get("pricing", {})
                prompt_price = float(pricing.get("prompt", -1))
                if prompt_price == 0 or ":free" in m.get("id", ""):
                    free_models.append(m["id"])

        return free_models

    except Exception as e:
        print(f"Ошибка при получении списка моделей: {e}")
        return []


def test_model(model_id):
    """Проверяет, работает ли модель"""
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "Привет"}],
                "max_tokens": 10
            },
            timeout=15
        )
        return resp.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    print("BARAVKO — Проверка доступных ИИ-моделей")
    print("-" * 50)

    free_models = get_free_models()
    print(f"Найдено бесплатных моделей: {len(free_models)}")

    if not free_models:
        print("Бесплатные модели не найдены или ошибка подключения")
        print("Проверь ключ OPENROUTER_API_KEY в .env")
        exit(1)

    print("\nТестируем модели...")
    working = []

    for model_id in free_models:
        print(f"  Тестирую {model_id}...", end=" ", flush=True)
        if test_model(model_id):
            print("✅ работает")
            working.append(model_id)
        else:
            print("❌ не работает")

    print(f"\nРабочие модели ({len(working)}):")
    for m in working:
        print(f"  - {m}")

    # Сохраняем результат в файл (опционально)
    with open("working_models.txt", "w", encoding="utf-8") as f:
        for m in working:
            f.write(m + "\n")

    print("\nСписок  рабочих моделей сохранён в working_models.txt")