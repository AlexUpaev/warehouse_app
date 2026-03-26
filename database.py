import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
from utils.password_helper import PasswordHelper

class Database:
    def __init__(self):
        self.config = Config().get_db_config()
    
    def get_connection(self):
        return psycopg2.connect(
            host=self.config["host"],
            port=self.config["port"],
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"]
        )
    
    def get_table_data(self, table_name: str):
        """Получает данные из таблицы и возвращает их в виде списка словарей."""
        queries = {
            "users": """
            SELECT id, login, full_name, email, role, is_active, created_at, last_login
            FROM users ORDER BY id
            """,
            "categories": """
            SELECT id, name, description, created_at
            FROM categories ORDER BY id
            """,
            "suppliers": """
            SELECT id, name, contact_person, phone, email, address, created_at
            FROM suppliers ORDER BY id
            """,
            # ✅ ИСПРАВЛЕНО - убран JOIN с suppliers, используется поле supplier напрямую
            "materials": """
            SELECT m.id, m.name, m.quantity, m.unit, m.price,
            m.min_quantity, m.supplier, m.description,
            c.name AS category_name,
            u.full_name AS created_by_name,
            m.created_at, m.updated_at
            FROM materials m
            LEFT JOIN categories c ON m.category_id = c.id
            LEFT JOIN users u ON m.created_by = u.id
            ORDER BY m.id
            """,
            "transactions": """
            SELECT t.id, mat.name AS material_name,
            u.full_name AS user_name,
            t.quantity, t.transaction_type,
            t.document_number, t.document_date, t.notes,
            t.created_at
            FROM transactions t
            LEFT JOIN materials mat ON t.material_id = mat.id
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            """,
            "material_history": """
            SELECT mh.id, mat.name AS material_name,
            mh.old_quantity, mh.new_quantity, mh.difference,
            mh.action_type, mh.notes,
            u.full_name AS changed_by_name,
            mh.changed_at
            FROM material_history mh
            JOIN materials mat ON mh.material_id = mat.id
            LEFT JOIN users u ON mh.changed_by = u.id
            ORDER BY mh.changed_at DESC
            """
        }
        
        if table_name not in queries:
            raise ValueError(f"Неизвестная таблица: {table_name}")
        
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(queries[table_name])
            rows = cursor.fetchall()
            return rows
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        def insert_record(self, table_name: str, data: dict):
            """Добавляет новую запись в таблицу."""
            keys = list(data.keys())
            values = tuple(data[key] for key in keys)
            columns = ', '.join(keys)
            placeholders = ', '.join(['%s'] * len(keys))
            sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            conn = None
            cursor = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(sql_query, values)
                conn.commit()
            except Exception as e:
                print(f"Ошибка при добавлении записи: {e}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
    
    def update_record(self, table_name: str, record_id: int, data: dict):
        """Обновляет запись в таблице по её уникальному идентификатору."""
        set_clause = ', '.join([f"{key}=%s" for key in data.keys()])
        values = tuple(data.values()) + (record_id,)
        sql_query = f"UPDATE {table_name} SET {set_clause} WHERE id=%s"
        
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            print(f"Ошибка при обновлении записи: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def delete_record(self, table_name: str, record_id: int):
        """Удаляет запись из таблицы по её уникальному идентификатору."""
        sql_query = f"DELETE FROM {table_name} WHERE id=%s"
        
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query, (record_id,))
            conn.commit()
        except Exception as e:
            print(f"Ошибка при удалении записи: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def check_login_exists(self, login):
        """Проверяет, существует ли указанный логин в базе данных."""
        query = "SELECT COUNT(*) FROM users WHERE login = %s;"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (login,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    
    def register_user(self, login, password, full_name, email=None):
        """Регистрирует нового пользователя в базе данных."""
        hashed_password = PasswordHelper.hash_password(password)
        query = """
        INSERT INTO users (login, password_hash, full_name, email)
        VALUES (%s, %s, %s, %s);
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (login, hashed_password, full_name, email))
            conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def authenticate_user(self, login, password):
        """Проверяет учетные данные пользователя и возвращает данные пользователя, если они валидны."""
        query = """
        SELECT id, login, full_name, email, role, is_active, created_at, last_login, password_hash
        FROM users
        WHERE login = %s AND is_active = TRUE
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (login,))
        user = cursor.fetchone()
        
        # ✅ ПРОВЕРКА ПАРОЛЯ И ОБНОВЛЕНИЕ last_login
        if user and PasswordHelper.verify_password(password, user[8]):
            # Обновляем время последнего входа
            update_query = """
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = %s
            """
            cursor.execute(update_query, (user[0],))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                'id': user[0],
                'login': user[1],
                'full_name': user[2],
                'email': user[3],
                'role': user[4],
                'is_active': user[5],
                'created_at': user[6],
                'last_login': user[7]
            }
        
        cursor.close()
        conn.close()
        return None