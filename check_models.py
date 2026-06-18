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
    """Получает список ВСЕХ моделей с нулевой ценой (бесплатных)"""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {KEY}"},
            timeout=30
        )
        data = resp.json()

        if isinstance(data, list):
            models = data
        elif isinstance(data, dict) and "data" in data:
            models = data["data"]
        else:
            print("Неожиданный формат ответа от API")
            return []

        free_models = []
        for m in models:
            if isinstance(m, dict):
                pricing = m.get("pricing", {})
                # Проверяем: и prompt, и completion стоят 0
                prompt_price = float(pricing.get("prompt", -1))
                completion_price = float(pricing.get("completion", -1))
                image_price = float(pricing.get("image", -1))

                # Модель бесплатна, если все цены 0
                is_free = (prompt_price == 0 and completion_price == 0) or image_price == 0

                if is_free:
                    model_id = m.get("id")
                    if model_id:
                        free_models.append(model_id)

        return free_models

    except Exception as e:
        print(f"Ошибка при получении списка моделей: {e}")
        return []


def test_model(model_id):
    """Проверяет, работает ли модель (отвечает ли на простой запрос)"""
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "OK"}],
                "max_tokens": 5
            },
            timeout=15
        )
        return resp.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    print("BARAVKO — Проверка доступных ИИ-моделей (поиск всех бесплатных)")
    print("-" * 60)

    free_models = get_free_models()
    print(f"Найдено бесплатных моделей (с ценой 0): {len(free_models)}")

    if not free_models:
        print("Бесплатные модели не найдены или ошибка подключения")
        print("\nВозможные причины:")
        print("1. Неправильный ключ OPENROUTER_API_KEY в .env")
        print("2. Проблемы с сетью (прокси/VPN)")
        print("3. API OpenRouter временно недоступен")
        exit(1)

    print("\nТестируем модели (это может занять некоторое время)...")
    working = []

    for i, model_id in enumerate(free_models):
        print(f"  [{i+1}/{len(free_models)}] {model_id}...", end=" ", flush=True)
        if test_model(model_id):
            print("✅ работает")
            working.append(model_id)
        else:
            print("❌ не работает")

    print(f"\n✅ Рабочие модели ({len(working)}):")
    for m in working:
        print(f"  - {m}")

    # Сохраняем результат в файл
    with open("working_models.txt", "w", encoding="utf-8") as f:
        for m in working:
            f.write(m + "\n")

    print(f"\nСписок рабочих моделей сохранён в working_models.txt")