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

CF_API_KEY = os.getenv('CLOUDFLARE_API_KEY')
CF_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
MESSAGE = "привет"

def test_cloudflare():
    """Тестирование Cloudflare Workers AI"""
    print("="*60)
    print("☁️ ТЕСТИРОВАНИЕ CLOUDFLARE WORKERS AI")
    print("="*60)
    
    if not CF_API_KEY or not CF_ACCOUNT_ID:
        print("❌ Не все ключи найдены в .env")
        print("💡 Нужно: CLOUDFLARE_API_KEY и CLOUDFLARE_ACCOUNT_ID")
        return {'status': 'error', 'error': 'no_key'}
    
    print(f"🔑 API Key: {CF_API_KEY[:15]}...")
    print(f"🏢 Account ID: {CF_ACCOUNT_ID[:10]}...")
    print(f"📝 Запрос: '{MESSAGE}'\n")
    
    models = [
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3-8b-instruct",
        "@cf/mistral/mistral-7b-instruct-v0.2",
        "@cf/meta/llama-2-7b-chat-int8",
        "@cf/google/gemma-2b-it-lora",
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "@cf/qwen/qwen1.5-7b-chat-awq",
        "@cf/tiiuae/falcon-7b-instruct",
    ]
    
    print(f"📋 Моделей: {len(models)}")
    for i, m in enumerate(models, 1):
        print(f"   {i}. {m}")
    
    print(f"\n🚀 Тестируем...\n")
    
    results = []
    
    for i, model_name in enumerate(models, 1):
        print(f"[{i}/{len(models)}] {model_name}")
        
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model_name}"
            
            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {CF_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    "messages": [{"role": "user", "content": MESSAGE}],
                    "max_tokens": 50
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    answer = result['result']['response']
                    answer_clean = answer.replace('\n', ' ')[:80]
                    print(f"     ✅ {answer_clean}...")
                    
                    results.append({
                        'model': model_name,
                        'status': 'success',
                        'response': answer
                    })
                else:
                    print(f"     ❌ {result.get('errors', 'Unknown')}")
                    
            elif response.status_code == 401:
                print(f"     ❌ Неверный токен")
                break
            else:
                print(f"     ❌ {response.status_code}")
        
        except Exception as e:
            print(f"     ❌ {str(e)[:50]}")
        
        time.sleep(0.3)
    
    print(f"\n{'='*60}")
    print("📊 ИТОГИ CLOUDFLARE")
    print("="*60)
    
    success = [r for r in results if r['status'] == 'success']
    print(f"✅ Работает: {len(success)}/{len(models)}")
    
    if success:
        print("\n✅ МОДЕЛИ:")
        for r in success:
            print(f"   • {r['model']}")
            print(f"     {r['response'][:80]}...")
    
    print("DEBUG Cloudflare: returning result")
    return {
        'total': len(models),
        'models': [r['model'] for r in success]
    }

if __name__ == "__main__":
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    result = test_cloudflare()
    print("\n✨ Готово!")
    print(f"DEBUG main: result = {result}")