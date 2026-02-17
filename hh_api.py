import requests
import json

def test_hh_api():
    """Тестовый запрос к HH API"""
    
    url = "https://api.hh.ru/vacancies"
    
    # Простые параметры
    params = {
        'text': 'аналитик данных',
        'area': 22,  # 22 - Владивосток
        'per_page': 5,
        'page': 0
    }
    
    # Важно: HeadHunter требует корректный User-Agent и email для связи
    headers = {
        'User-Agent': 'MyVacancyParser/1.0 (4t3w35g@gmail.com)',
        'Accept': 'application/json',
        'HH-User-Agent': 'MyVacancyParser/1.0 (4t3w35g@gmail.com)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Найдено вакансий: {data.get('found', 0)}")
            print(f"Страниц: {data.get('pages', 0)}")
            
            # Выведем первую вакансию
            items = data.get('items', [])
            if items:
                print(f"\nПоказано вакансий: {len(items)}")
                for i, item in enumerate(items[:3]):  # Показать первые 3
                    print(f"\n{i+1}. ID: {item.get('id')}")
                    print(f"   Название: {item.get('name')}")
                    print(f"   Компания: {item.get('employer', {}).get('name')}")
                    
                    # Проверим доступность детальной информации
                    vacancy_id = item.get('id')
                    if vacancy_id:
                        detail_url = f"{url}/{vacancy_id}"
                        detail_response = requests.get(detail_url, headers=headers)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            salary = detail_data.get('salary')
                            if salary:
                                salary_from = salary.get('from', '?')
                                salary_to = salary.get('to', '?')
                                currency = salary.get('currency', '')
                                print(f"   Зарплата: {salary_from} - {salary_to} {currency}")
                            else:
                                print(f"   Зарплата: не указана")
                            
                            # Выводим опыт работы
                            experience = detail_data.get('experience', {}).get('name', 'не указан')
                            print(f"   Опыт: {experience}")
                            
                            # Выводим дату публикации
                            published_at = detail_data.get('published_at', '')
                            print(f"   Опубликовано: {published_at}")
                        else:
                            print(f"   Детали: ошибка {detail_response.status_code}")
        else:
            print(f"Ошибка: {response.text}")
            
    except Exception as e:
        print(f"Исключение: {e}")

if __name__ == "__main__":
    test_hh_api()