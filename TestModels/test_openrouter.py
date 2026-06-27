import os
import requests
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MESSAGE = "привет"

def get_free_models():
    """Получаем список ВСЕХ бесплатных моделей"""
    print("🔍 Получаем список бесплатных моделей...")
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}'},
            timeout=(5, 15)
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения списка: {response.status_code}")
            return []
        
        models_data = response.json().get('data', [])
        print(f"📊 Всего моделей в каталоге: {len(models_data)}")
        
        free_models = []
        for m in models_data:
            pricing = m.get('pricing', {})
            prompt_price = float(pricing.get('prompt', 1))
            completion_price = float(pricing.get('completion', 1))
            
            if prompt_price == 0 and completion_price == 0:
                free_models.append({
                    'id': m['id'],
                    'name': m.get('name', m['id']),
                    'context': m.get('context_length', '?'),
                    'description': m.get('description', '')[:100]
                })
        
        print(f"🎉 Найдено бесплатных моделей: {len(free_models)}")
        
        print("\n📋 Список бесплатных моделей:")
        print("="*80)
        for i, model in enumerate(free_models, 1):
            print(f"{i:2}. {model['name']}")
            print(f"    ID: {model['id']}")
            print(f"    Контекст: {model['context']:,}")
            if model['description']:
                print(f"    📝 {model['description']}...")
            print()
        
        return free_models
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def test_model(model, index, total):
    """Тестируем одну модель"""
    model_id = model['id']
    model_name = model['name']
    
    print(f"\n[{index}/{total}] Тестируем: {model_name}")
    print(f"    ID: {model_id}")
    
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:3000',
        'X-Title': 'API Test'
    }
    
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": MESSAGE}],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=(5, 10)  # 5 сек на connect, 10 сек на read
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            answer_clean = answer.replace('\n', ' ').replace('\r', ' ')
            usage = result.get('usage', {})
            
            print(f"    ✅ ОТВЕТ: {answer_clean[:120]}...")
            if usage:
                print(f"    📊 Токены: {usage.get('total_tokens', '?')}")
            
            return {
                'status': 'success',
                'response': answer,
                'usage': usage
            }
            
        elif response.status_code == 429:
            print(f"    ⚠️ Лимит запросов")
            return {'status': 'rate_limited'}
                
        elif response.status_code == 402:
            print(f"    💰 Требует оплаты")
            return {'status': 'payment_required'}
            
        elif response.status_code == 404:
            print(f"    ❌ Не найдена")
            return {'status': 'not_found'}
            
        else:
            print(f"    ❌ Ошибка {response.status_code}")
            return {'status': 'error', 'code': response.status_code}
            
    except requests.exceptions.Timeout:
        print(f"    ⏰ Таймаут (пропущена)")
        return {'status': 'timeout'}
        
    except requests.exceptions.ConnectionError:
        print(f"    🔌 Ошибка соединения")
        return {'status': 'error', 'message': 'connection_error'}
        
    except Exception as e:
        error_str = str(e)[:80]
        print(f"    ❌ {error_str}")
        return {'status': 'error', 'message': error_str}

def test_all_free_models():
    """Тестируем ВСЕ бесплатные модели без вопросов"""
    print("="*60)
    print("🔄 ТЕСТИРОВАНИЕ OPENROUTER")
    print("="*60)
    
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY не найден в .env")
        return {'status': 'error', 'error': 'no_key'}
    
    free_models = get_free_models()
    
    if not free_models:
        print("❌ Нет моделей для тестирования")
        return {'status': 'error', 'error': 'no_models'}
    
    models_to_test = free_models
    
    print(f"\n🚀 Тестируем все {len(models_to_test)} моделей...")
    print("="*80)
    
    results = {
        'success': [],
        'rate_limited': [],
        'payment_required': [],
        'not_found': [],
        'error': [],
        'timeout': []
    }
    
    start_time = datetime.now()
    
    for i, model in enumerate(models_to_test, 1):
        result = test_model(model, i, len(models_to_test))
        
        if result['status'] == 'success':
            results['success'].append({**model, **result})
        elif result['status'] == 'rate_limited':
            results['rate_limited'].append(model)
        elif result['status'] == 'payment_required':
            results['payment_required'].append(model)
        elif result['status'] == 'not_found':
            results['not_found'].append(model)
        elif result['status'] == 'timeout':
            results['timeout'].append(model)
        else:
            results['error'].append(model)
        
        time.sleep(0.2)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ OPENROUTER")
    print("="*80)
    print(f"⏰ Время тестирования: {elapsed:.0f} сек")
    print(f"📝 Протестировано моделей: {len(models_to_test)}")
    print()
    print(f"✅ Успешно: {len(results['success'])}")
    print(f"⚠️ Лимит запросов: {len(results['rate_limited'])}")
    print(f"💰 Требуют оплаты: {len(results['payment_required'])}")
    print(f"❌ Не найдены: {len(results['not_found'])}")
    print(f"⏰ Таймаут: {len(results['timeout'])}")
    print(f"❌ Ошибки: {len(results['error'])}")
    
    if results['success']:
        print("\n✅ РАБОТАЮЩИЕ МОДЕЛИ:")
        print("-"*80)
        for model in results['success']:
            print(f"\n📌 {model['name']}")
            print(f"   ID: {model['id']}")
            print(f"   Ответ: {model['response'][:150]}...")
            if model.get('usage'):
                print(f"   Токены: {model['usage'].get('total_tokens', '?')}")
    
    if results['rate_limited']:
        print(f"\n💡 Модели с лимитом ({len(results['rate_limited'])} шт) - попробуйте позже")
    
    return {
        'total': len(models_to_test),
        'models': [m['name'] for m in results['success']]
    }

if __name__ == "__main__":
    print(f"📝 Тестовый запрос: '{MESSAGE}'")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_all_free_models()
    
    print("\n✨ Готово!")