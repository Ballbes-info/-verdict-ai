import requests
import os
from dotenv import load_dotenv

load_dotenv()
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")

if not AUTH_KEY:
    print("❌ Ошибка: не найден GIGACHAT_AUTH_KEY в .env файле")
    exit(1)


def get_gigachat_token():
    response = requests.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": "12345678-1234-1234-1234-123456789012",
            "Authorization": f"Basic {AUTH_KEY}"
        },
        data={"scope": "GIGACHAT_API_PERS"},
        verify=False
    )
    return response.json().get("access_token")


def ask_gigachat(prompt, system_prompt=None, temperature=0.7, max_tokens=500):
    token = get_gigachat_token()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json={
            "model": "GigaChat",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        verify=False
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка: {response.status_code}"


# ============================================================
# ИГРОК ВВОДИТ ДЕЛО
# ============================================================

def create_case():
    print("\n📋 СОЗДАНИЕ ДЕЛА")
    topic = input("Тема дела: ")
    defendant = input("Обвиняемый: ")
    charges = input("Обвинение: ")

    print("\nВведите улики (каждую с новой строки, пустая строка - конец):")
    evidence = []
    while True:
        line = input("- ")
        if not line:
            break
        evidence.append(line)

    defense = input("\nПозиция защиты: ")

    return {
        "topic": topic,
        "defendant": defendant,
        "charges": charges,
        "evidence": evidence,
        "defense": defense
    }


def get_case_context(case):
    return f"""
ДЕЛО: {case['topic']}
ОБВИНЯЕМЫЙ: {case['defendant']}
ОБВИНЕНИЕ: {case['charges']}
УЛИКИ (ТОЛЬКО ЭТИ, НЕ ПРИДУМЫВАЙ НОВЫЕ):
{chr(10).join(['- ' + e for e in case['evidence']])}
ПОЗИЦИЯ ЗАЩИТЫ: {case['defense']}

ВАЖНО: Ты НЕ МОЖЕШЬ придумывать новые улики, свидетелей или факты. Используй ТОЛЬКО то, что перечислено выше. Не выходи за рамки дела!"""


# ============================================================
# ПРОМПТЫ
# ============================================================

def get_prosecutor_prompt(case):
    return f"""Ты — государственный прокурор.

{get_case_context(case)}

Твоя задача — доказать вину подсудимого, используя ТОЛЬКО перечисленные улики.
Ты НЕ МОЖЕШЬ придумывать новых фактов.
Отвечай кратко. Если аргумент защиты слаб — укажи на это, но не выдумывай."""


def get_judge_final_prompt(case):
    return f"""Ты — судья.

{get_case_context(case)}

Твоя задача — проанализировать аргументы сторон и вынести вердикт.
Ты НЕ МОЖЕШЬ придумывать новые факты.
Используй ТОЛЬКО те улики и аргументы, которые были в процессе."""


# ============================================================
# ЗАПУСК СУДА
# ============================================================

def run_trial(case, max_rounds=3):
    print(f"\n⚖️ ДЕЛО: {case['topic']}")
    print(f"👤 ОБВИНЯЕМЫЙ: {case['defendant']}")
    print(f"📜 ОБВИНЕНИЕ: {case['charges']}")
    print("\n🔍 УЛИКИ:")
    for e in case['evidence']:
        print(f"  - {e}")
    print(f"\n🛡️ ЗАЩИТА: {case['defense']}")
    print("\n" + "=" * 50 + "\n")

    full_history = []
    player_message = input("👨‍💼 Адвокат (вы): ")

    for round_num in range(1, max_rounds + 1):
        print(f"\n--- РАУНД {round_num} ---")
        if round_num > 1:
            player_message = input("👨‍💼 Адвокат (вы): ")
        full_history.append({"role": "адвокат", "content": player_message})

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in full_history])
        prosecutor_prompt = f"""
{get_case_context(case)}

История суда:
{history_text}

Прокурор, опровергни последний аргумент адвоката.
Используй ТОЛЬКО улики из дела.
НЕ ПРИДУМЫВАЙ НОВЫХ ФАКТОВ."""

        print("⚡ Прокурор думает...")
        prosecutor_response = ask_gigachat(
            prosecutor_prompt,
            system_prompt=get_prosecutor_prompt(case)
        )
        print(f"⚡ Прокурор: {prosecutor_response}")
        full_history.append({"role": "прокурор", "content": prosecutor_response})

        if input("\nПродолжить? (да/нет): ").lower() != "да":
            break

    print("\n" + "=" * 50)
    print("⚖️ ВЕРДИКТ")

    transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in full_history])
    verdict_prompt = f"""
{get_case_context(case)}

СТЕНОГРАММА:
{transcript}

Судья, вынеси вердикт, используя ТОЛЬКО факты из дела и аргументы сторон.
НЕ ПРИДУМЫВАЙ НОВЫХ ФАКТОВ."""

    verdict = ask_gigachat(verdict_prompt, system_prompt=get_judge_final_prompt(case))
    print(f"👨‍⚖️ {verdict}")
    print("\n⚖️ Суд окончен.")


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    case = create_case()
    run_trial(case, max_rounds=3)