from flask import Flask, request, jsonify
import redis
import json
import uuid
import time

app = Flask(__name__)
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route('/analyze_url', methods=['POST'])
def analyze_url():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Invalid request, 'url' is required."}), 400
        
        url = data['url']
        if not isinstance(url, str) or len(url.strip()) == 0:
            return jsonify({"error": "URL must be a non-empty string."}), 400
        
        # Создаем уникальный ID для задачи
        task_id = str(uuid.uuid4())
        
        # Отправляем задачу в очередь
        task_data = {
            'task_id': task_id,
            'url': url.strip()
        }
        
        redis_client.lpush('url_analysis_queue', json.dumps(task_data))
        
        # Ждем результат (с таймаутом)
        result = None
        timeout = 30  # 30 секунд
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result_data = redis_client.get(f'result:{task_id}')
            if result_data:
                result = json.loads(result_data)
                # Удаляем результат из Redis после получения
                redis_client.delete(f'result:{task_id}')
                break
            time.sleep(0.1)
        
        if result is None:
            return jsonify({"error": "Analysis timeout. Please try again."}), 408
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """Получение общей статистики анализа URL"""
    try:
        stats_data = redis_client.get('url_stats')
        if stats_data:
            stats = json.loads(stats_data)
            return jsonify(stats), 200
        else:
            return jsonify({"message": "No statistics available yet"}), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving stats: {str(e)}"}), 500

@app.route('/queue_status', methods=['GET'])
def queue_status():
    """Получение информации о состоянии очереди"""
    try:
        queue_length = redis_client.llen('url_analysis_queue')
        
        # Получаем информацию о результатах в Redis
        result_keys = redis_client.keys('result:*')
        pending_results = len(result_keys)
        
        return jsonify({
            "queue_length": queue_length,
            "pending_results": pending_results,
            "status": "healthy" if queue_length < 100 else "overloaded"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error getting queue status: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 