from flask import Flask, jsonify, request
import mysql.connector
import os
import redis
import time
import logging

app = Flask(__name__)

# Configure structured logging format
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Timer for measuring request duration
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def log_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        app.logger.info(f"Path: {request.path} | Method: {request.method} | Status: {response.status_code} | Time: {duration:.4f}s")
    return response

# Health check route for Rahti liveness and readiness probes
@app.route('/healthz')
def healthz():
    return jsonify({"status": "healthy"}), 200

# Redis connection setup
cache = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'redis-service'),
    port=6379,
    decode_responses=True
)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'database'),
        user=os.environ.get('DB_USER', 'appuser'),
        password=os.environ.get('DB_PASSWORD', 'changeme'),
        database=os.environ.get('DB_NAME', 'appdb')
    )

@app.route('/api')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("INSERT INTO visitors () VALUES ()")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM visitors")
        visitor_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT NOW()")
        db_time = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Connected to Database Successfully!",
            "visitor_count": visitor_count,
            "db_time": str(db_time)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/cache')
def cache_demo():
    try:
        views = cache.incr('page_views')
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Assignment 6 - Cloud Services</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; background-color: #f4f7f6; color: #333; line-height: 1.6; }}
                .container {{ max-width: 950px; margin: 0 auto; background: #fff; padding: 35px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #27ae60; padding-bottom: 12px; margin-top: 0; }}
                .card {{ background: #e8f8f5; border-left: 5px solid #27ae60; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                .counter {{ font-size: 2.2em; color: #27ae60; font-weight: bold; font-family: monospace; margin: 10px 0 0 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Weekly Assignment 6: CI/CD & Observability</h1>
                <div class="card">
                    <h2>Redis Cache Counter</h2>
                    <p class="counter">Total Hits: {views}</p>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return jsonify({"error": "Redis connection failed", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)