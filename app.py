import logging
import time
from flask import Flask, jsonify, g
from db import get_connection

# 1. Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] in %(module)s: %(message)s",
    handlers=[
        logging.StreamHandler(),          # Outputs to console/Docker logs
        logging.FileHandler("app.log")   # Saves logs to a local file
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 2. Database Connection Management Hooks
@app.before_request
def before_request():
    """Opens a secure DB connection before handling the route request."""
    g.start_time = time.time()
    try:
        g.db_conn = get_connection()
        logger.debug("Database connection successfully established for request.")
    except Exception as e:
        logger.error(f"Database connection initiation failed: {str(e)}")
        g.db_conn = None

@app.after_request
def after_request(response):
    """Closes the connection after the route completes and logs response time."""
    # Safely close connection if it exists
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        db_conn.close()
        logger.debug("Database connection safely closed.")
        
    # Log total API processing duration
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"Request completed in {duration:.4f} seconds | Status: {response.status_code}")
        
    return response

# 3. Centralized Application Error Handling
@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Catches crashes, logs the full trace, and keeps the app running."""
    logger.exception(f"Unhandled Exception encountered: {str(error)}")
    return jsonify({
        "status": "error",
        "message": "An internal server error occurred."
    }), 500

# 4. Production Ready Application Routes
@app.route("/")
def home():
    if not g.db_conn:
        raise Exception("Database connection unavailable for this request.")

    # Using context manager for cursor ensures automatic cleanup
    with g.db_conn.cursor() as cur:
        query = "SELECT version();"
        
        # Track individual query performance
        query_start = time.time()
        cur.execute(query)
        version = cur.fetchone()
        query_duration = time.time() - query_start
        
        # Log the specific query metrics
        logger.info(f"Executed SQL: '{query}' | Duration: {query_duration:.4f}s")

    return jsonify({
        "status": "success",
        "database": "PostgreSQL",
        "version": version[0]
    })

@app.route("/health")
def health():
    """Advanced health check that verifies the app AND the live DB path."""
    status_code = 200
    health_report = {"status": "UP", "database_connectivity": "OK"}
    
    if not g.db_conn:
        status_code = 503
        health_report["status"] = "DOWN"
        health_report["database_connectivity"] = "FAILED"
        logger.critical("Health check failed: Database backend is unreachable.")
    else:
        try:
            with g.db_conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        except Exception as e:
            status_code = 503
            health_report["status"] = "DOWN"
            health_report["database_connectivity"] = f"ERROR: {str(e)}"
            logger.critical(f"Health check query failed: {str(e)}")

    return jsonify(health_report), status_code

if __name__ == "__main__":
    # In production, use a WSGI server like Gunicorn instead of app.run()
    app.run(host="0.0.0.0", port=5000, debug=False)

