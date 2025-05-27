import redis
import json
import time
from urllib.parse import urlparse, parse_qs
import re
import tldextract

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Список подозрительных доменных зон
SUSPICIOUS_TLDS = [
    'tk', 'ml', 'ga', 'cf', 'bit', 'short', 'tiny', 'click', 'download'
]

# Список популярных социальных сетей
SOCIAL_DOMAINS = [
    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
    'youtube.com', 'tiktok.com', 'vk.com', 'telegram.org'
]

def analyze_url(url):
    """Анализирует URL и возвращает подробную информацию"""
    
    try:
        # Базовый парсинг URL
        parsed = urlparse(url)
        
        # Извлечение домена и поддомена
        extracted = tldextract.extract(url)
        
        # Проверка валидности
        is_valid = bool(parsed.netloc and parsed.scheme)
        
        # Анализ схемы
        is_secure = parsed.scheme == 'https'
        
        # Парсинг GET параметров
        query_params = parse_qs(parsed.query)
        param_count = len(query_params)
        
        # Анализ пути
        path_segments = [seg for seg in parsed.path.split('/') if seg]
        path_depth = len(path_segments)
        
        # Проверка на подозрительность
        is_suspicious = extracted.suffix.lower() in SUSPICIOUS_TLDS
        
        # Определение типа сайта
        site_type = "unknown"
        full_domain = f"{extracted.domain}.{extracted.suffix}".lower()
        
        if full_domain in SOCIAL_DOMAINS:
            site_type = "social_media"
        elif extracted.suffix in ['gov', 'edu']:
            site_type = "institutional"
        elif extracted.suffix in ['com', 'org', 'net']:
            site_type = "commercial"
        
        # Анализ длины URL
        url_length = len(url)
        if url_length > 200:
            length_category = "very_long"
        elif url_length > 100:
            length_category = "long"
        elif url_length > 50:
            length_category = "medium"
        else:
            length_category = "short"
        
        # Поиск потенциально опасных паттернов
        dangerous_patterns = []
        if re.search(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', parsed.netloc):
            dangerous_patterns.append("ip_address_instead_domain")
        if len(extracted.subdomain.split('.')) > 2:
            dangerous_patterns.append("multiple_subdomains")
        if re.search(r'[^a-zA-Z0-9\-\.]', parsed.netloc):
            dangerous_patterns.append("special_chars_in_domain")
        
        result = {
            "is_valid": is_valid,
            "components": {
                "scheme": parsed.scheme,
                "domain": extracted.domain,
                "subdomain": extracted.subdomain,
                "tld": extracted.suffix,
                "full_domain": full_domain,
                "path": parsed.path,
                "query": parsed.query,
                "fragment": parsed.fragment,
                "port": parsed.port
            },
            "analysis": {
                "is_secure": is_secure,
                "url_length": url_length,
                "length_category": length_category,
                "path_depth": path_depth,
                "param_count": param_count,
                "site_type": site_type,
                "is_suspicious": is_suspicious,
                "dangerous_patterns": dangerous_patterns
            },
            "parameters": query_params,
            "security_score": calculate_security_score(
                is_secure, is_suspicious, dangerous_patterns, url_length
            )
        }
        
        # Обновляем статистику
        update_statistics(extracted.suffix, site_type, is_secure)
        
        return result
        
    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Failed to parse URL: {str(e)}",
            "components": {},
            "analysis": {},
            "parameters": {},
            "security_score": 0
        }

def calculate_security_score(is_secure, is_suspicious, dangerous_patterns, url_length):
    """Вычисляет оценку безопасности URL от 0 до 100"""
    score = 50  # базовая оценка
    
    if is_secure:
        score += 20
    else:
        score -= 15
    
    if is_suspicious:
        score -= 25
    
    score -= len(dangerous_patterns) * 10
    
    if url_length > 200:
        score -= 10
    elif url_length < 50:
        score += 5
    
    return max(0, min(100, score))

def update_statistics(tld, site_type, is_secure):
    """Обновляет общую статистику анализа"""
    try:
        stats_data = redis_client.get('url_stats')
        if stats_data:
            stats = json.loads(stats_data)
        else:
            stats = {
                "total_analyzed": 0,
                "tld_distribution": {},
                "site_type_distribution": {},
                "security_stats": {"secure": 0, "insecure": 0}
            }
        
        stats["total_analyzed"] += 1
        
        # Статистика по доменным зонам
        if tld in stats["tld_distribution"]:
            stats["tld_distribution"][tld] += 1
        else:
            stats["tld_distribution"][tld] = 1
        
        # Статистика по типам сайтов
        if site_type in stats["site_type_distribution"]:
            stats["site_type_distribution"][site_type] += 1
        else:
            stats["site_type_distribution"][site_type] = 1
        
        # Статистика безопасности
        if is_secure:
            stats["security_stats"]["secure"] += 1
        else:
            stats["security_stats"]["insecure"] += 1
        
        redis_client.setex('url_stats', 3600, json.dumps(stats))  # Храним час
        
    except Exception as e:
        print(f"Error updating statistics: {e}")

def process_tasks():
    """Основной цикл обработки задач"""
    print("URL Analyzer Worker started, waiting for tasks...")
    
    while True:
        try:
            # Получаем задачу из очереди (блокирующий вызов)
            task_data = redis_client.brpop('url_analysis_queue', timeout=1)
            
            if task_data:
                # Парсим данные задачи
                task_json = json.loads(task_data[1])
                task_id = task_json['task_id']
                url = task_json['url']
                
                print(f"Processing task {task_id}: {url}")
                
                # Выполняем анализ
                result = analyze_url(url)
                
                # Сохраняем результат в Redis
                redis_client.setex(f'result:{task_id}', 60, json.dumps(result))
                
                print(f"Task {task_id} completed")
                
        except Exception as e:
            print(f"Error processing task: {e}")
            time.sleep(1)

if __name__ == '__main__':
    process_tasks() 