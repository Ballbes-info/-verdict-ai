import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import requests
import time

project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MESSAGE = "привет"

def test_mistral():
    """Тестирование Mistral API"""
    print("="*60)
    print("🌬️ ТЕСТИРОВАНИЕ MISTRAL AI")
    print("="*60)
    
    if not MISTRAL_API_KEY:
        print("❌ MISTRAL_API_KEY не найден в .env")
        print("💡 Получите ключ: https://console.mistral.ai")
        return {'status': 'error', 'error': 'no_key'}
    
    masked_key = MISTRAL_API_KEY[:10] + "..." + MISTRAL_API_KEY[-5:] if len(MISTRAL_API_KEY) > 15 else "***"
    print(f"🔑 Ключ: {masked_key}")
    print(f"📝 Запрос: '{MESSAGE}'\n")
    
    # Бесплатные модели Mistral
    models = [
        "mistral-small-latest",
        "mistral-medium-latest",
        "mistral-large-latest",
        "open-mistral-nemo",
        "ministral-8b-latest",
        "ministral-3b-latest",
    ]
    
    print(f"📋 Моделей: {len(models)}")
    for i, m in enumerate(models, 1):
        print(f"   {i}. {m}")
    
    print(f"\n🚀 Тестируем...\n")
    
    results = []
    
    for i, model_id in enumerate(models, 1):
        print(f"[{i}/{len(models)}] {model_id}")
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    'Authorization': f'Bearer {MISTRAL_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": MESSAGE}],
                    "max_tokens": 50
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                answer_clean = answer.replace('\n', ' ')[:80]
                usage = result.get('usage', {})
                
                print(f"     ✅ {answer_clean}...")
                
                if usage:
                    print(f"     📊 Токены: {usage.get('total_tokens', '?')}")
                
                results.append({
                    'model': model_id,
                    'status': 'success',
                    'response': answer
                })
                
            elif response.status_code == 401:
                print(f"     ❌ Неверный ключ")
                break
            elif response.status_code == 402:
                print(f"     💰 Нужна оплата")
            elif response.status_code == 429:
                print(f"     ⚠️ Лимит")
                time.sleep(2)
            else:
                print(f"     ❌ {response.status_code}")
        
        except Exception as e:
            print(f"     ❌ {str(e)[:50]}")
        
        time.sleep(0.3)
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ MISTRAL")
    print("="*60)
    
    success = [r for r in results if r['status'] == 'success']
    print(f"✅ Работает: {len(success)}/{len(models)}")
    
    if success:
        print("\n✅ МОДЕЛИ:")
        for r in success:
            print(f"   • {r['model']}")
            print(f"     {r['response'][:80]}...")
    
    print("DEBUG: about to return from test_mistral")
    return {
        'total': len(models),
        'models': [r['model'] for r in success]
    }

if __name__ == "__main__":
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    result = test_mistral()
    print("\n✨ Готово!")
    print("DEBUG main: result =", result)