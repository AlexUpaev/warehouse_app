# utils/permissions.py
"""
Модуль управления правами доступа
"""

ROLE_PERMISSIONS = {
    "admin": {
        "tables": [
            "Пользователи",
            "Категории",
            "Поставщики",
            "Материалы",
            "Транзакции",
            "История изменений"
        ],
        "can_edit": True,
        "can_delete": True,
        "can_import_export": True,
        "can_reset_password": True,
        "can_view_all_tables": True
    },
    "user": {
        "tables": [
            "Категории",
            "Поставщики",
            "Материалы"
        ],
        "can_edit": True,
        "can_delete": False,
        "can_import_export": False,
        "can_reset_password": False,
        "can_view_all_tables": False
    }
}

def get_user_permissions(role: str) -> dict:
    """Возвращает права для указанной роли"""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["user"])

def can_access_table(role: str, table_name: str) -> bool:
    """Проверяет, есть ли доступ к таблице"""
    perms = get_user_permissions(role)
    return table_name in perms["tables"]

def can_edit(role: str) -> bool:
    """Проверяет право на редактирование"""
    return get_user_permissions(role)["can_edit"]

def can_delete(role: str) -> bool:
    """Проверяет право на удаление"""
    return get_user_permissions(role)["can_delete"]

def can_import_export(role: str) -> bool:
    """Проверяет право на импорт/экспорт"""
    return get_user_permissions(role)["can_import_export"]

def can_reset_password(role: str) -> bool:
    """Проверяет право на сброс пароля"""
    return get_user_permissions(role)["can_reset_password"]