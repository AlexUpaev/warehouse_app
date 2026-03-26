# diagnostic.py
import psycopg2
from config import Config

config = Config()
db_config = config.get_db_config()
print("Текущие настройки:")
for key, value in db_config.items():
    print(f"  {key}: {value}")

# Пробуем подключиться к разным базам
test_databases = ["warehouse_db", "postgres", "template1"]

for db in test_databases:
    print(f"\nПопытка подключения к базе '{db}':")
    try:
        test_config = db_config.copy()
        test_config["database"] = db
        conn = psycopg2.connect(**test_config)
        print(f"  ✅ Успешно подключен к {db}")
        conn.close()
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
