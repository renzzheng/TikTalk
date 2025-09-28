import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from contextlib import contextmanager

class DatabaseService:
    def __init__(self):
        self.connection_params = None

    def init_app(self):
        """Initialize DB connection parameters lazily from env vars"""
        self.connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            if not self.connection_params:
                self.init_app()
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute a database query"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)

                    if fetch_one:
                        result = cursor.fetchone()
                        conn.commit()  # Commit after fetching data
                        return {'success': True, 'data': dict(result) if result else None}
                    elif fetch_all:
                        results = cursor.fetchall()
                        conn.commit()  # Commit after fetching data
                        return {'success': True, 'data': [dict(row) for row in results]}
                    else:
                        conn.commit()
                        return {'success': True, 'message': 'Query executed successfully'}
        except Exception as e:
            logging.error(f"Query execution error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def test_connection(self):
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1 as test", fetch_one=True)
            return result['success']
        except Exception as e:
            logging.error(f"Database connection test failed: {str(e)}")
            return False

db_service = DatabaseService()
