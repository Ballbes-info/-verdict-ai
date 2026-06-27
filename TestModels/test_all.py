import sys
from pathlib import Path
from datetime import datetime
import builtins
import traceback

sys.path.insert(0, str(Path(__file__).parent))

original_input = builtins.input
def auto_input(prompt=""):
    if "y/n" in prompt.lower():
        return "y"
    return ""
builtins.input = auto_input

from test_gigachat import test_gigachat
from test_gemini import test_gemini  
from test_groq import test_groq
from test_cerebras import test_cerebras
from test_openrouter import test_all_free_models as test_openrouter
from test_github import test_github
from test_mistral import test_mistral
from test_cloudflare import test_cloudflare

DOCS_DIR = Path(__file__).parent.parent / 'docs'
RESULTS_FILE = DOCS_DIR / 'models_report.txt'

SERVICE_KEYS = {
    'GigaChat': 'GIGACHAT_AUTH_KEY',
    'Gemini': 'GEMINI_API_KEY',
    'Groq': 'GROQ_API_KEY',
    'OpenRouter': 'OPENROUTER_API_KEY',
    'Cerebras': 'CEREBRAS_API_KEY',
    'GitHub': 'GITHUB_API_KEY',
    'Mistral': 'MISTRAL_API_KEY',
    'Cloudflare': 'CLOUDFLARE_API_KEY',
}

report_data = {}

def safe_test(name, test_func):
    try:
        result = test_func()
        
        if result is None:
            print(f"DEBUG {name}: returned None")
            return {'service': name, 'key_name': SERVICE_KEYS.get(name, 'unknown'), 
                    'status': 'ok_no_data', 'models': [], 'total': 0}
        
        if isinstance(result, dict):
            models = result.get('models', [])
            print(f"DEBUG {name}: got dict with {len(models)} models: {models}")
            return {'service': name, 'key_name': SERVICE_KEYS.get(name, 'unknown'),
                    'status': 'ok', 'models': models, 'total': result.get('total', len(models))}
        
        print(f"DEBUG {name}: unknown type {type(result)} = {str(result)[:100]}")
        return {'service': name, 'key_name': SERVICE_KEYS.get(name, 'unknown'),
                'status': 'ok_no_data', 'models': [], 'total': 0}
    except Exception as e:
        print(f"DEBUG {name}: EXCEPTION {e}")
        return {'service': name, 'key_name': SERVICE_KEYS.get(name, 'unknown'),
                'status': 'error', 'error': str(e)[:100], 'models': []}

def run_all():
    print("="*60)
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    DOCS_DIR.mkdir(exist_ok=True)
    
    tests = [
        ("GigaChat", test_gigachat),
        ("Gemini", test_gemini),
        ("Groq", test_groq),
        ("OpenRouter", test_openrouter),
        ("Cerebras", test_cerebras),
        ("GitHub", test_github),
        ("Mistral", test_mistral),
        ("Cloudflare", test_cloudflare),
    ]
    
    for name, test_func in tests:
        print(f"\n▶️  {name}...")
        result = safe_test(name, test_func)
        report_data[name] = result
    
    builtins.input = original_input
    analyze_models()
    generate_report()
    print_summary()

def analyze_models():
    for service, data in report_data.items():
        if data.get('status') == 'error':
            continue
        
        models = data.get('models', [])
        if not models:
            continue
        
        key_name = data.get('key_name', 'unknown')
        
        analyzed = []
        for model_name in models:
            name_lower = model_name.lower()
            
            if any(x in name_lower for x in ['70b', '72b', '405b', 'large', 'gpt-4o', '120b', 'ultra', 'super']):
                strength = '⭐⭐⭐⭐⭐'
            elif any(x in name_lower for x in ['32b', '34b', 'medium', 'gpt-3.5', 'scout']):
                strength = '⭐⭐⭐⭐'
            elif any(x in name_lower for x in ['8b', '9b', 'small', 'mini', 'nemo']):
                strength = '⭐⭐⭐'
            elif any(x in name_lower for x in ['3b', '1.5b', 'tiny']):
                strength = '⭐⭐'
            else:
                strength = '⭐⭐⭐'
            
            if 'groq' in service.lower():
                speed = '⚡ Мгновенно'
            elif 'cloudflare' in service.lower():
                speed = '⚡ Быстро'
            elif 'mistral' in service.lower():
                speed = '🚀 Быстро'
            elif 'cerebras' in service.lower():
                speed = '🚀 Быстро'
            else:
                speed = '🕐 Средне'
            
            if any(x in name_lower for x in ['compound', '405b', 'ultra', 'large', 'super', '120b']):
                tokens = '💰 Затратная'
            elif any(x in name_lower for x in ['70b', '72b']):
                tokens = '💲 Средняя'
            elif any(x in name_lower for x in ['8b', '9b', 'small', 'mini', '3b', '1.5b']):
                tokens = '🆓 Экономная'
            else:
                tokens = '💲 Средняя'
            
            if 'gigachat' in service.lower():
                rus = '✅ Родной'
            elif any(x in name_lower for x in ['gpt', 'gemini', 'llama-3.3', 'qwen', 'mistral', 'glm']):
                rus = '✅ Хорошо'
            else:
                rus = '⚠️ Средне'
            
            analyzed.append({
                'name': model_name,
                'service': service,
                'key': key_name,
                'strength': strength,
                'speed': speed,
                'tokens': tokens,
                'russian': rus
            })
        
        report_data[service]['analyzed'] = analyzed

def generate_report():
    all_models = []
    for data in report_data.values():
        if data.get('analyzed'):
            all_models.extend(data['analyzed'])
    
    working_services = sum(1 for v in report_data.values() if v.get('analyzed'))
    
    report = f"""╔══════════════════════════════════════════════════════════╗
║     РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ AI API                     ║
║     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚══════════════════════════════════════════════════════════╝

СЕРВИСОВ: {working_services}/{len(report_data)} работает
МОДЕЛЕЙ: {len(all_models)} доступно

{'='*60}
РЕЙТИНГ МОДЕЛЕЙ:
{'='*60}
"""
    
    all_models.sort(key=lambda x: len(x['strength']), reverse=True)
    
    for i, m in enumerate(all_models, 1):
        report += f"""
{i:2}. {m['name']}
    Сервис:    {m['service']}
    Ключ:      {m['key']}
    Сила:      {m['strength']}
    Скорость:  {m['speed']}
    Токены:    {m['tokens']}
    Русский:   {m['russian']}
"""
    
    strongest = [m for m in all_models if '⭐⭐⭐⭐⭐' in m['strength']]
    economical = [m for m in all_models if 'Экономная' in m['tokens']]
    fast = [m for m in all_models if 'Мгновенно' in m['speed']]
    russian = [m for m in all_models if 'Родной' in m['russian'] or 'Хорошо' in m['russian']]
    
    report += f"""
{'='*60}
КАТЕГОРИИ:
{'='*60}

🏆 САМЫЕ СИЛЬНЫЕ ({len(strongest)}):
"""
    for m in strongest:
        report += f"   • {m['name']} ← {m['key']}\n"
    
    report += f"""
⚡ САМЫЕ БЫСТРЫЕ ({len(fast)}):
"""
    for m in fast:
        report += f"   • {m['name']} ← {m['key']}\n"
    
    report += f"""
🆓 ЭКОНОМНЫЕ ({len(economical)}):
"""
    for m in economical:
        report += f"   • {m['name']} ← {m['key']}\n"
    
    report += f"""
🌍 ЛУЧШИЕ ДЛЯ РУССКОГО ({len(russian)}):
"""
    for m in russian[:10]:
        report += f"   • {m['name']} ← {m['key']}\n"
    
    report += f"""
{'='*60}
РЕКОМЕНДАЦИИ:
{'='*60}

💡 Сложные задачи → ⭐⭐⭐⭐⭐ модели
💡 Скорость → Groq (⚡ Мгновенно)
💡 Экономия → 🆓 Экономные модели
💡 Русский → GigaChat, Gemini, Groq, Mistral

⚠️ Все лимиты общие на сервис, не на модель!

Последняя проверка: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

def print_summary():
    print("\n" + "="*50)
    print("📊 ИТОГИ")
    print("="*50)
    
    for service, data in report_data.items():
        if data.get('analyzed'):
            models = [m['name'] for m in data['analyzed']]
            print(f"✅ {service:12} {len(models)} моделей")
        elif data.get('status') == 'ok_no_data':
            print(f"⚠️ {service:12} работает (нет данных о моделях)")
        else:
            error = data.get('error', 'неизвестно')
            print(f"❌ {service:12} {error[:40]}")
    
    print(f"\n💾 Отчет: {RESULTS_FILE}")
    print("✨ Готово!")

if __name__ == "__main__":
    run_all()