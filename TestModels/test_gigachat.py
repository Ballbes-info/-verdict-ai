import os
import requests
from dotenv import load_dotenv
import urllib3
from datetime import datetime

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGACHAT_AUTH_KEY = os.getenv('GIGACHAT_AUTH_KEY')
MESSAGE = "привет"

def get_token():
    auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': '550e8400-e29b-41d4-a716-446655440000',
        'Authorization': f'Basic {GIGACHAT_AUTH_KEY}'
    }
    auth_data = {'scope': 'GIGACHAT_API_PERS'}
    response = requests.post(auth_url, headers=auth_headers, data=auth_data, verify=False)
    if response.status_code == 200:
        token_data = response.json()
        return {'access_token': token_data.get('access_token'), 'expires_at': token_data.get('expires_at')}
    return None

def get_limits(access_token):
    try:
        limits_url = "https://gigachat.devices.sberbank.ru/api/v1/limits"
        headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
        response = requests.get(limits_url, headers=headers, verify=False)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def test_gigachat():
    print("="*60)
    print("🤖 ТЕСТИРОВАНИЕ GIGACHAT")
    print("="*60)
    
    if not GIGACHAT_AUTH_KEY:
        print("❌ GIGACHAT_AUTH_KEY не найден в .env")
        return {'status': 'error', 'error': 'no_key'}
    
    try:
        from gigachat import GigaChat
        print("📚 Используем библиотеку gigachat\n")
        
        with GigaChat(credentials=GIGACHAT_AUTH_KEY, verify_ssl_certs=False) as giga:
            response = giga.chat(MESSAGE)
            answer = response.choices[0].message.content
            
            print("📤 Ответ:")
            print(f"   {answer}\n")
            
            usage = response.usage
            if usage:
                print("📊 Использование токенов:")
                print(f"   Запрос: {usage.prompt_tokens}")
                print(f"   Ответ: {usage.completion_tokens}")
                print(f"   Всего: {usage.total_tokens}")
            
            return {'total': 1, 'models': ['GigaChat (Сбер)']}
            
    except ImportError:
        print("⚠️ Библиотека gigachat не установлена")
    
    try:
        token_info = get_token()
        if not token_info:
            return {'status': 'error', 'error': 'auth_failed'}
        
        access_token = token_info['access_token']
        
        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        chat_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        chat_data = {"model": "GigaChat", "messages": [{"role": "user", "content": MESSAGE}]}
        
        chat_response = requests.post(chat_url, headers=chat_headers, json=chat_data, verify=False)
        
        if chat_response.status_code == 200:
            return {'total': 1, 'models': ['GigaChat (Сбер)']}
        else:
            return {'status': 'error', 'error': f'http_{chat_response.status_code}'}
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)[:80]}

if __name__ == "__main__":
    test_gigachat()