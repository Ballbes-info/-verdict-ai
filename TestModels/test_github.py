import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import requests
import time

# Ищем .env в корне проекта
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
MESSAGE = "привет"

def get_github_models():
    """Получаем модели и конвертируем в короткие имена"""
    print("🔍 Получаем список моделей GitHub...")
    
    try:
        url = "https://models.inference.ai.azure.com/models"
        headers = {'Authorization': f'Bearer {GITHUB_API_KEY}'}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            models = response.json()
            print(f"📊 Всего моделей в API: {len(models)}")
            
            model_mapping = {
                'gpt-4o-mini': 'gpt-4o-mini',
                'gpt-4o': 'gpt-4o',
                'gpt-4': 'gpt-4',
                'gpt-3.5-turbo': 'gpt-3.5-turbo',
                'Meta-Llama-3.3-70B-Instruct': 'Meta-Llama-3.3-70B-Instruct',
                'Meta-Llama-3.1-8B-Instruct': 'Meta-Llama-3.1-8B-Instruct',
                'Meta-Llama-3.1-70B-Instruct': 'Meta-Llama-3.1-70B-Instruct',
                'Meta-Llama-3.1-405B-Instruct': 'Meta-Llama-3.1-405B-Instruct',
                'Llama-3.2-3B-Instruct': 'Llama-3.2-3B-Instruct',
                'Llama-3.2-11B-Vision-Instruct': 'Llama-3.2-11B-Vision-Instruct',
                'Llama-3.2-90B-Vision-Instruct': 'Llama-3.2-90B-Vision-Instruct',
                'Meta-Llama-3-8B-Instruct': 'Meta-Llama-3-8B-Instruct',
                'Meta-Llama-3-70B-Instruct': 'Meta-Llama-3-70B-Instruct',
                'Phi-3.5-mini-instruct': 'Phi-3.5-mini-instruct',
                'Phi-3.5-MoE-instruct': 'Phi-3.5-MoE-instruct',
                'Phi-3-mini-4k-instruct': 'Phi-3-mini-4k-instruct',
                'Phi-3-mini-128k-instruct': 'Phi-3-mini-128k-instruct',
                'Phi-3-small-8k-instruct': 'Phi-3-small-8k-instruct',
                'Phi-3-medium-4k-instruct': 'Phi-3-medium-4k-instruct',
                'Phi-3-medium-128k-instruct': 'Phi-3-medium-128k-instruct',
                'Mistral-large': 'Mistral-large',
                'Mistral-small': 'Mistral-small',
                'Mistral-Nemo': 'Mistral-Nemo',
                'Mistral-7B-Instruct-v0.3': 'Mistral-7B-Instruct-v0.3',
                'Cohere-command-r': 'Cohere-command-r',
                'Cohere-command-r-plus': 'Cohere-command-r-plus',
                'AI21-Jamba-1.5-Large': 'AI21-Jamba-1.5-Large',
                'AI21-Jamba-1.5-Mini': 'AI21-Jamba-1.5-Mini',
                'DeepSeek-R1': 'DeepSeek-R1',
                'DeepSeek-V3': 'DeepSeek-V3',
            }
            
            found_models = []
            for model in models:
                name = model.get('name', '')
                model_id = model.get('id', '')
                
                for short_name in model_mapping:
                    if short_name.lower() in name.lower() or short_name.lower() in model_id.lower():
                        if short_name not in [m['id'] for m in found_models]:
                            found_models.append({
                                'id': short_name,
                                'name': name,
                                'full_id': model_id
                            })
                            break
            
            print(f"📊 Найдено коротких имен: {len(found_models)}")
            return found_models
        
        return []
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return []

def get_popular_models():
    """Все доступные модели GitHub Models"""
    return [
        # OpenAI
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4", "name": "GPT-4"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        
        # Meta
        {"id": "Meta-Llama-3.3-70B-Instruct", "name": "Llama 3.3 70B"},
        {"id": "Meta-Llama-3.1-8B-Instruct", "name": "Llama 3.1 8B"},
        {"id": "Meta-Llama-3.1-70B-Instruct", "name": "Llama 3.1 70B"},
        {"id": "Meta-Llama-3.1-405B-Instruct", "name": "Llama 3.1 405B"},
        {"id": "Llama-3.2-3B-Instruct", "name": "Llama 3.2 3B"},
        {"id": "Llama-3.2-11B-Vision-Instruct", "name": "Llama 3.2 11B Vision"},
        {"id": "Llama-3.2-90B-Vision-Instruct", "name": "Llama 3.2 90B Vision"},
        {"id": "Meta-Llama-3-8B-Instruct", "name": "Llama 3 8B"},
        {"id": "Meta-Llama-3-70B-Instruct", "name": "Llama 3 70B"},
        
        # Microsoft
        {"id": "Phi-3.5-mini-instruct", "name": "Phi-3.5 Mini"},
        {"id": "Phi-3.5-MoE-instruct", "name": "Phi-3.5 MoE"},
        {"id": "Phi-3-mini-4k-instruct", "name": "Phi-3 Mini 4K"},
        {"id": "Phi-3-mini-128k-instruct", "name": "Phi-3 Mini 128K"},
        {"id": "Phi-3-small-8k-instruct", "name": "Phi-3 Small 8K"},
        {"id": "Phi-3-medium-4k-instruct", "name": "Phi-3 Medium 4K"},
        {"id": "Phi-3-medium-128k-instruct", "name": "Phi-3 Medium 128K"},
        
        # Mistral
        {"id": "Mistral-large", "name": "Mistral Large"},
        {"id": "Mistral-small", "name": "Mistral Small"},
        {"id": "Mistral-Nemo", "name": "Mistral Nemo"},
        {"id": "Mistral-7B-Instruct-v0.3", "name": "Mistral 7B v0.3"},
        
        # Cohere
        {"id": "Cohere-command-r", "name": "Command R"},
        {"id": "Cohere-command-r-plus", "name": "Command R+"},
        
        # AI21
        {"id": "AI21-Jamba-1.5-Large", "name": "Jamba 1.5 Large"},
        {"id": "AI21-Jamba-1.5-Mini", "name": "Jamba 1.5 Mini"},
        
        # DeepSeek
        {"id": "DeepSeek-R1", "name": "DeepSeek R1"},
        {"id": "DeepSeek-V3", "name": "DeepSeek V3"},
        
        # Embedding
        {"id": "text-embedding-3-small", "name": "Embedding Small"},
        {"id": "text-embedding-3-large", "name": "Embedding Large"},
        {"id": "Cohere-embed-v3-english", "name": "Cohere Embed English"},
        {"id": "Cohere-embed-v3-multilingual", "name": "Cohere Embed Multi"},
    ]

def test_github():
    """Тестирование GitHub Models API"""
    print("="*60)
    print("🐙 ТЕСТИРОВАНИЕ GITHUB MODELS")
    print("="*60)
    
    if not GITHUB_API_KEY:
        print("❌ GITHUB_API_KEY не найден в .env")
        return {'status': 'error', 'error': 'no_key'}
    
    masked_key = GITHUB_API_KEY[:15] + "..." + GITHUB_API_KEY[-5:]
    print(f"🔑 Токен: {masked_key}")
    print(f"📝 Запрос: '{MESSAGE}'\n")
    
    # Пробуем получить модели через API
    models = get_github_models()
    
    # Если через API не получилось - используем полный список
    if not models:
        print("🔄 Используем полный список моделей...\n")
        models = get_popular_models()
    
    # Показываем список
    print(f"📋 Моделей для проверки: {len(models)}")
    for i, model in enumerate(models, 1):
        print(f"   {i:2}. {model['id']}")
    
    # Тестируем все без input
    models_to_test = models
    
    print(f"\n🚀 Тестируем {len(models_to_test)} моделей...\n")
    print(f"{'№':<4} {'Статус':<8} {'Модель':<45} {'Ответ'}")
    print("-"*100)
    
    results = []
    success_count = 0
    
    for i, model in enumerate(models_to_test, 1):
        model_id = model['id']
        
        try:
            url = "https://models.inference.ai.azure.com/chat/completions"
            headers = {
                'Authorization': f'Bearer {GITHUB_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": model_id,
                "messages": [{"role": "user", "content": MESSAGE}],
                "max_tokens": 50
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                answer_clean = answer.replace('\n', ' ')[:60]
                
                print(f"{i:<4} {'✅':<8} {model_id[:45]:<45} {answer_clean}")
                success_count += 1
                
                results.append({
                    'model': model_id,
                    'status': 'success',
                    'response': answer,
                    'usage': result.get('usage', {})
                })
                
            elif response.status_code == 429:
                print(f"{i:<4} {'⚠️':<8} {model_id[:45]:<45} [Лимит запросов]")
                time.sleep(2)
                
            elif response.status_code == 400:
                print(f"{i:<4} {'❌':<8} {model_id[:45]:<45} [Не найдена]")
                
            elif response.status_code == 401 or response.status_code == 403:
                print(f"{i:<4} {'🔒':<8} {model_id[:45]:<45} [Нет доступа]")
                
            else:
                print(f"{i:<4} {'❌':<8} {model_id[:45]:<45} [Ошибка {response.status_code}]")
            
        except Exception as e:
            print(f"{i:<4} {'❌':<8} {model_id[:45]:<45} [{str(e)[:30]}]")
        
        time.sleep(0.3)
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ GITHUB MODELS")
    print("="*60)
    print(f"✅ Успешно: {success_count}/{len(models_to_test)}")
    print(f"📝 Всего в каталоге: {len(models)}")
    
    if success_count > 0:
        print(f"\n✅ РАБОТАЮЩИЕ МОДЕЛИ:")
        for r in results:
            if r['status'] == 'success':
                print(f"   • {r['model']}")
                print(f"     {r['response'][:80]}...")
    
    return {
        'total': len(models_to_test),
        'models': [r['model'] for r in results if r['status'] == 'success']
    }

if __name__ == "__main__":
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    test_github()
    print("\n✨ Готово!")