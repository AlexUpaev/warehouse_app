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
        queries = {
            "users": "SELECT id, login, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY id",
            "categories": "SELECT id, name, description, created_at FROM categories ORDER BY id",
            "suppliers": "SELECT id, name, contact_person, phone, email, address, created_at FROM suppliers ORDER BY id",
            "materials": """
                SELECT m.id, m.name, m.quantity, m.unit, m.price, m.min_quantity, m.supplier, m.description,
                c.name AS category_name, u.full_name AS created_by_name, m.created_at, m.updated_at
                FROM materials m
                LEFT JOIN categories c ON m.category_id = c.id
                LEFT JOIN users u ON m.created_by = u.id
                ORDER BY m.id
            """,
            "transactions": """
                SELECT t.id, mat.name AS material_name, u.full_name AS user_name,
                t.quantity, t.transaction_type, t.document_number, t.document_date, t.notes, t.created_at
                FROM transactions t
                LEFT JOIN materials mat ON t.material_id = mat.id
                LEFT JOIN users u ON t.user_id = u.id
                ORDER BY t.created_at DESC
            """,
            "material_history": """
                SELECT mh.id, mat.name AS material_name, mh.old_quantity, mh.new_quantity, mh.difference,
                mh.action_type, mh.notes, u.full_name AS changed_by_name, mh.changed_at
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
            if cursor: cursor.close()
            if conn: conn.close()

    def get_foreign_key_dependencies(self, table_name: str, record_id: int):
        """
        🔍 Находит все таблицы, которые ссылаются на удаляемую запись через внешний ключ.
        Возвращает словарь: {имя_таблицы_на_русском: количество_записей}
        """
        dependencies = {}
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Запрос к information_schema для поиска внешних ключей, ссылающихся на нашу таблицу
            query = """
                SELECT 
                    tc.table_name AS referencing_table,
                    kcu.column_name AS referencing_column
                FROM 
                    information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu 
                        ON rc.constraint_name = kcu.constraint_name
                    JOIN information_schema.table_constraints tc 
                        ON kcu.constraint_name = tc.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON rc.unique_constraint_name = ccu.constraint_name
                WHERE 
                    tc.constraint_type = 'FOREIGN KEY'
                    AND ccu.table_name = %s
                    AND ccu.column_name = 'id'
                    AND tc.table_schema = 'public'
            """
            cursor.execute(query, (table_name,))
            foreign_keys = cursor.fetchall()
            
            for fk_row in foreign_keys:
                fk_table = fk_row[0]
                fk_column = fk_row[1]
                
                # Пропускаем самопересечения
                if fk_table == table_name:
                    continue
                    
                # Считаем, сколько записей ссылается на удаляемый ID
                check_query = f"SELECT COUNT(*) FROM {fk_table} WHERE {fk_column} = %s"
                cursor.execute(check_query, (record_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    table_names_ru = {
                        'users': 'Пользователи',
                        'categories': 'Категории',
                        'suppliers': 'Поставщики',
                        'materials': 'Материалы',
                        'transactions': 'Транзакции',
                        'material_history': 'История материалов',
                        'import_queue': 'Очередь импорта',
                    }
                    table_name_ru = table_names_ru.get(fk_table, fk_table)
                    dependencies[table_name_ru] = count
            
            return dependencies
            
        except Exception as e:
            print(f"❌ Ошибка при проверке зависимостей: {e}")
            return {}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def cascade_delete(self, table_name: str, record_id: int):
        """
        🗑️ Каскадное удаление: сначала удаляем зависимые записи, затем основную.
        Возвращает словарь с количеством удалённых записей по таблицам.
        """
        deleted_counts = {}
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Получаем список зависимых таблиц
            query = """
                SELECT 
                    tc.table_name AS referencing_table,
                    kcu.column_name AS referencing_column
                FROM 
                    information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu 
                        ON rc.constraint_name = kcu.constraint_name
                    JOIN information_schema.table_constraints tc 
                        ON kcu.constraint_name = tc.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON rc.unique_constraint_name = ccu.constraint_name
                WHERE 
                    tc.constraint_type = 'FOREIGN KEY'
                    AND ccu.table_name = %s
                    AND ccu.column_name = 'id'
                    AND tc.table_schema = 'public'
            """
            cursor.execute(query, (table_name,))
            foreign_keys = cursor.fetchall()
            
            # Удаляем записи из зависимых таблиц
            for fk_row in foreign_keys:
                fk_table = fk_row[0]
                fk_column = fk_row[1]
                
                if fk_table == table_name:
                    continue
                    
                delete_query = f"DELETE FROM {fk_table} WHERE {fk_column} = %s"
                cursor.execute(delete_query, (record_id,))
                if cursor.rowcount > 0:
                    table_names_ru = {
                        'users': 'Пользователи',
                        'categories': 'Категории',
                        'suppliers': 'Поставщики',
                        'materials': 'Материалы',
                        'transactions': 'Транзакции',
                        'material_history': 'История материалов',
                        'import_queue': 'Очередь импорта',
                    }
                    table_name_ru = table_names_ru.get(fk_table, fk_table)
                    deleted_counts[table_name_ru] = cursor.rowcount
            
            # Удаляем основную запись
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            table_names_ru_singular = {
                'users': 'Пользователь',
                'categories': 'Категория',
                'suppliers': 'Поставщик',
                'materials': 'Материал',
                'transactions': 'Транзакция',
                'material_history': 'Запись истории',
            }
            table_name_ru = table_names_ru_singular.get(table_name, table_name)
            deleted_counts[table_name_ru] = 1
            
            conn.commit()
            return deleted_counts
            
        except Exception as e:
            print(f"❌ Ошибка при каскадном удалении: {e}")
            if conn: conn.rollback()
            return {}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def insert_record(self, table_name: str, data: dict):
        if not data:
            return
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
            print(f"❌ Ошибка при добавлении записи: {e}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def update_record(self, table_name: str, record_id: int, data: dict):
        if not data:
            return
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
            print(f"❌ Ошибка при обновлении записи: {e}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def delete_record(self, table_name: str, record_id: int):
        """Простое удаление без каскада (для случаев, когда зависимостей нет)"""
        sql_query = f"DELETE FROM {table_name} WHERE id=%s"
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query, (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка при удалении записи: {e}")
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def check_login_exists(self, login):
        query = "SELECT COUNT(*) FROM users WHERE login = %s;"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (login,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0

    def register_user(self, login, password, full_name, email=None):
        hashed_password = PasswordHelper.hash_password(password)
        query = "INSERT INTO users (login, password_hash, full_name, email) VALUES (%s, %s, %s, %s);"
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (login, hashed_password, full_name, email))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при регистрации пользователя: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def authenticate_user(self, login, password):
        query = """
        SELECT id, login, full_name, email, role, is_active, created_at, last_login, password_hash
        FROM users WHERE login = %s AND is_active = TRUE
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (login,))
        user = cursor.fetchone()
        
        if user and PasswordHelper.verify_password(password, user[8]):
            update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
            cursor.execute(update_query, (user[0],))
            conn.commit()
            cursor.close()
            conn.close()
            return {
                'id': user[0], 'login': user[1], 'full_name': user[2], 'email': user[3],
                'role': user[4], 'is_active': user[5], 'created_at': user[6], 'last_login': user[7]
            }
        
        cursor.close()
        conn.close()
        return None

    def update_user_password(self, user_id: int, new_password_hash: str):
        query = "UPDATE users SET password_hash = %s WHERE id = %s"
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (new_password_hash, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при обновлении пароля: {e}")
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()