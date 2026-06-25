import psycopg2

def get_connection():
    return psycopg2.connect(
        host="172.17.0.1",
        database="pythonapp",
        user="test",
        password="test123",
        port="5432"
    )
