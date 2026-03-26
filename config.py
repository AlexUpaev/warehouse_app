# config.py
import json
from pathlib import Path

class Config:
    def __init__(self):
        # Используем Path вместо строки, чтобы можно было вызывать .exists()
        self.config_file = Path.home() / ".warehouse_config.json"
    
    def get_db_config(self):
        """Получает настройки БД из файла или возвращает значения по умолчанию"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при чтении конфигурации: {e}")
        
        return {
            "host": "localhost",
            "port": 5432,
            "database": "warehouse_db",
            "user": "postgres",
            "password": "root"
        }
    
    def save_db_config(self, db_config):
        """Сохраняет настройки БД в файл"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(db_config, f, indent=4)
