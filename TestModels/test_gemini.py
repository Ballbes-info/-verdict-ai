import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"📁 .env найден: {env_path}")
else:
    load_dotenv()
    print("📁 .env ищется в текущей папке")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MESSAGE = "привет"

def test_gemini():
    """Тестирование Gemini API"""
    print("="*60)
    print("🌟 ТЕСТИРОВАНИЕ GOOGLE GEMINI")
    print("="*60)
    
    print(f"🔍 Поиск ключа...")
    print(f"   Путь к .env: {env_path}")
    print(f"   Файл существует: {env_path.exists()}")
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY не найден!")
        return {'status': 'error', 'error': 'no_key'}
    
    masked_key = GEMINI_API_KEY[:10] + "..." + GEMINI_API_KEY[-5:]
    print(f"🔑 Ключ найден: {masked_key}")
    print(f"📝 Запрос: '{MESSAGE}'")
    
    try:
        import google.generativeai as genai
        
        print("🔑 Авторизация...")
        genai.configure(api_key=GEMINI_API_KEY)
        
        print("🔄 Модель: gemini-2.5-flash")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("📤 Отправляем запрос...")
        response = model.generate_content(MESSAGE)
        
        print(f"\n✅ ОТВЕТ:")
        print(f"   {response.text}")
        
        print("\n✅ Gemini РАБОТАЕТ!")
        
        return {'total': 1, 'models': ['gemini-2.5-flash']}
        
    except ImportError:
        print("❌ Установите: pip install google-generativeai")
        return {'status': 'error', 'error': 'no_library'}
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:150]}")
        return {'status': 'error', 'error': str(e)[:80]}

if __name__ == "__main__":
    test_gemini()