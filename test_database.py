"""
Тест для проверки получения и форматирования дат из БД
"""
from database import Database
from datetime import date, datetime
from dateutil import tz

def test_database_dates():
    print("=" * 60)
    print("ТЕСТ ОТОБРАЖЕНИЯ ДАТ")
    print("=" * 60)
    
    db = Database()
    
    # Тестируем все таблицы с датами
    tables_with_dates = {
        "users": ["created_at", "last_login"],
        "categories": ["created_at"],
        "materials": ["created_at", "updated_at"],
        "transactions": ["document_date", "created_at"],
        "material_history": ["changed_at"]
    }
    
    for table_name, date_fields in tables_with_dates.items():
        print(f"\n📊 Таблица: {table_name}")
        print("-" * 60)
        
        try:
            rows = db.get_table_data(table_name)
            print(f"✅ Получено записей: {len(rows)}")
            
            if not rows:
                print("⚠️  Таблица пустая")
                continue
            
            # Берем первую строку
            row = rows[0]
            print(f"\nТип строки: {type(row)}")
            print(f"Ключи: {list(row.keys())}")
            
            # Проверяем каждое поле с датой
            for field in date_fields:
                if field in row:
                    value = row[field]
                    print(f"\  🔹 Поле '{field}':")
                    print(f"     Значение: {value}")
                    print(f"     Тип: {type(value)}")
                    
                    if value is None:
                        print(f"     ⚠️  Значение NULL")
                    elif isinstance(value, datetime):
                        print(f"     ✅ Это datetime")
                        print(f"     Timezone: {value.tzinfo}")
                        try:
                            if value.tzinfo is not None:
                                local_value = value.astimezone(tz.tzlocal())
                            else:
                                local_value = value
                            formatted = local_value.strftime("%d.%m.%Y %H:%M")
                            print(f"     Форматировано: {formatted}")
                        except Exception as e:
                            print(f"     ❌ Ошибка форматирования: {e}")
                    elif isinstance(value, date):
                        print(f"     ✅ Это date (без времени)")
                        formatted = value.strftime("%d.%m.%Y")
                        print(f"     Форматировано: {formatted}")
                    else:
                        print(f"     ⚠️  Неожиданный тип: {type(value)}")
                else:
                    print(f"\  ⚠️  Поле '{field}' не найдено в строке")
                    
        except Exception as e:
            print(f"❌ Ошибка при работе с таблицей {table_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    test_database_dates()