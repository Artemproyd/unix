#!/usr/bin/env python3

import requests

print("📝 Анализатор текста (введите 'q' для выхода)")

while True:
    text = input("\nТекст: ").strip()
    if text.lower() == 'q':
        break
    
    try:
        r = requests.post("http://localhost:8080/analyze", json={"text": text})
        data = r.json()
        
        if data.get('success'):
            print(f"Символы: {data['chars']}")
            print(f"Слова: {data['words']} (уникальных: {data['unique_words']})")
            print(f"Буквы: {data['letters']}")
            print(f"Частые слова: {data['top_words']}")
            print(f"Частые буквы: {data['top_letters']}")
            print(f"🔧 Обработано: {data['processed_by']}")
        else:
            print(f"Ошибка: {data.get('error')}")
    except:
        print("Ошибка подключения") 