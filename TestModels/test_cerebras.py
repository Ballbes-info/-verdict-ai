import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import requests

# Ищем .env в корне проекта
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
MESSAGE = "привет"

def test_cerebras():
    """Тестирование Cerebras API"""
    print("="*60)
    print("🧠 ТЕСТИРОВАНИЕ CEREBRAS")
    print("="*60)
    
    if not CEREBRAS_API_KEY:
        print("❌ CEREBRAS_API_KEY не найден в .env")
        return {'status': 'error', 'error': 'no_key'}
    
    masked_key = CEREBRAS_API_KEY[:10] + "..." + CEREBRAS_API_KEY[-5:] if len(CEREBRAS_API_KEY) > 15 else "***"
    print(f"🔑 Ключ: {masked_key}")
    print(f"📝 Запрос: '{MESSAGE}'\n")
    
    # Сначала получаем список доступных моделей
    print("🔍 Получаем список доступных моделей...")
    
    try:
        response = requests.get(
            "https://api.cerebras.ai/v1/models",
            headers={'Authorization': f'Bearer {CEREBRAS_API_KEY}'}
        )
        
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            
            print(f"📊 Доступно моделей: {len(models)}")
            
            working_models = []
            
            for model in models:
                model_id = model['id']
                print(f"\n🔄 Тестируем: {model_id}")
                
                # Тестируем модель
                data = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": MESSAGE}],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
                
                print("   📤 Отправляем запрос...")
                resp = requests.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={
                        'Authorization': f'Bearer {CEREBRAS_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json=data,
                    timeout=30
                )
                
                if resp.status_code == 200:
                    try:
                        result = resp.json()
                        answer = result['choices'][0]['message']['content']
                        usage = result.get('usage', {})
                        
                        print(f"   ✅ ОТВЕТ: {answer[:120]}...")
                        
                        if usage:
                            print(f"   📊 Токены: {usage.get('total_tokens', '?')}")
                        
                        print(f"   ✅ Cerebras ({model_id}) РАБОТАЕТ!")
                        working_models.append(model_id)
                    except:
                        print(f"   ⚠️ Ошибка парсинга ответа")
                else:
                    print(f"   ❌ Ошибка {resp.status_code}: {resp.text[:100]}")
            
            return {
                'total': len(models),
                'models': working_models
            }
        else:
            print(f"❌ Ошибка получения моделей: {response.status_code}")
            print(f"   {response.text[:200]}")
            return {'status': 'error', 'error': f'http_{response.status_code}'}
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'status': 'error', 'error': str(e)[:80]}

if __name__ == "__main__":
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    test_cerebras()
    print("\n✨ Готово!")