import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MESSAGE = "привет"

def test_groq():
    """Тестирование ВСЕХ доступных моделей Groq"""
    print("="*60)
    print("⚡ ТЕСТИРОВАНИЕ GROQ (ВСЕ МОДЕЛИ)")
    print("="*60)
    
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY не найден в .env")
        return {'status': 'error', 'error': 'no_key'}
    
    masked_key = GROQ_API_KEY[:10] + "..." + GROQ_API_KEY[-5:] if len(GROQ_API_KEY) > 15 else "***"
    print(f"🔑 Ключ: {masked_key}")
    print(f"📝 Запрос: '{MESSAGE}'")
    
    try:
        from groq import Groq
        
        print("📚 Библиотека groq установлена")
        client = Groq(api_key=GROQ_API_KEY)
        
        # Получаем список ВСЕХ моделей через API
        print("\n🔍 Получаем список доступных моделей...")
        
        try:
            models_list = client.models.list()
            all_models = [m.id for m in models_list.data]
            print(f"📊 Доступно моделей: {len(all_models)}")
            
            for i, m in enumerate(all_models, 1):
                print(f"   {i}. {m}")
        except:
            print("⚠️ Не удалось получить список, используем все известные модели")
            all_models = [
                'llama-3.3-70b-versatile',
                'gemma2-9b-it',
                'llama-3.1-8b-instant',
                'llama3-70b-8192',
                'llama3-8b-8192',
            ]
        
        print(f"\n🚀 Тестируем все {len(all_models)} моделей...\n")
        
        results = []
        
        for model_name in all_models:
            print(f"🔄 Модель: {model_name}")
            print("   📤 Отправляем запрос...")
            
            try:
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": MESSAGE}],
                    model=model_name,
                    temperature=0.7,
                    max_tokens=50
                )
                
                answer = completion.choices[0].message.content
                usage = completion.usage
                
                print(f"   ✅ ОТВЕТ: {answer[:80]}...")
                
                if usage:
                    print(f"   📊 Токены: {usage.total_tokens} (запрос: {usage.prompt_tokens}, ответ: {usage.completion_tokens})")
                    if hasattr(usage, 'total_time'):
                        print(f"   ⏱️ Время: {usage.total_time:.2f}с")
                
                print(f"   ✅ РАБОТАЕТ!")
                
                results.append({
                    'model': model_name,
                    'status': 'success',
                    'response': answer,
                    'usage': {
                        'total': usage.total_tokens if usage else '?',
                        'prompt': usage.prompt_tokens if usage else '?',
                        'completion': usage.completion_tokens if usage else '?'
                    }
                })
                
            except Exception as e:
                error_str = str(e)
                if 'does not support' in error_str.lower():
                    print(f"   ⏭️ Не для чата")
                elif 'decommissioned' in error_str.lower():
                    print(f"   ⚠️ Снята с поддержки")
                else:
                    print(f"   ❌ Ошибка: {error_str[:80]}")
            
            print()
            time.sleep(0.3)
        
        # Итоги
        print("="*60)
        print("📊 ИТОГИ GROQ")
        print("="*60)
        
        success = [r for r in results if r['status'] == 'success']
        errors = [r for r in results if r['status'] == 'error']
        
        print(f"✅ Работает: {len(success)}/{len(all_models)}")
        print(f"❌ Ошибок: {len(errors)}/{len(all_models)}")
        
        if success:
            print("\n✅ РАБОТАЮЩИЕ МОДЕЛИ:")
            for r in success:
                print(f"   • {r['model']}")
                print(f"     {r['response'][:80]}...")
                print(f"     Токены: {r['usage']['total']}")
        
        print("DEBUG GROQ: returning result")
        return {
            'total': len(all_models),
            'models': [r['model'] for r in success]
        }
        
    except ImportError:
        print("❌ Установите: pip install groq")
        return {'status': 'error', 'error': 'no_library'}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'status': 'error', 'error': str(e)[:80]}

if __name__ == "__main__":
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    result = test_groq()
    print(f"\n✨ Готово!")
    print(f"DEBUG main: result = {result}")