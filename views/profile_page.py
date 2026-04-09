from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtGui import QFont
from database import Database
from utils.password_helper import PasswordHelper


class ProfilePage(QMainWindow):
    back_to_table = Signal()
    
    # Основной цвет компании
    PRIMARY_COLOR = "#1A529C"
    PRIMARY_DARK = "#0d47a1"
    PRIMARY_LIGHT = "#E3F2FD"
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.menu_opened = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Личный кабинет | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # ─── Верхняя панель ──────────────────────────────────────
        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet(f"""
            background-color: {self.PRIMARY_LIGHT}; 
            border-bottom: 2px solid {self.PRIMARY_COLOR};
        """)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 20, 0)

        back_button = QPushButton("← Назад к таблицам")
        back_button.setFixedSize(180, 36)
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {self.PRIMARY_COLOR}; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 13px; 
            }} 
            QPushButton:hover {{ 
                background-color: {self.PRIMARY_DARK}; 
            }}
        """)
        back_button.clicked.connect(self.go_back)
        top_layout.addWidget(back_button)

        title_label = QLabel(f"Личный кабинет: {self.user_data['full_name']}")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.PRIMARY_COLOR};")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        logout_button = QPushButton("Выйти")
        logout_button.setFixedSize(80, 32)
        logout_button.setStyleSheet("""
            QPushButton { 
                background-color: #6C757D; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #5A6268; 
            }
        """)
        logout_button.clicked.connect(self.logout)
        top_layout.addWidget(logout_button)

        self.content_layout.addWidget(top_panel)

        # ─── Скролл с контентом ──────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background-color: #FAFAFA;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #FAFAFA;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        scroll_layout.setSpacing(20)

        # ─── Группа: Информация о пользователе ───────────────────
        info_group = self._create_group_box("📋 Информация о пользователе")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)

        created_at = str(self.user_data.get('created_at', 'N/A'))[:10] if self.user_data.get('created_at') else 'N/A'
        last_login = str(self.user_data.get('last_login', 'N/A'))[:19] if self.user_data.get('last_login') else 'N/A'

        for label, value in [
            ("ID", str(self.user_data.get('id', 'N/A'))),
            ("Логин", self.user_data.get('login', 'N/A')),
            ("ФИО", self.user_data.get('full_name', 'N/A')),
            ("Email", self.user_data.get('email', 'N/A') or 'Не указан'),
            ("Роль", self.user_data.get('role', 'N/A')),
            ("Статус", "✅ Активен" if self.user_data.get('is_active') else "❌ Неактивен"),
            ("Дата регистрации", created_at),
            ("Последний вход", last_login if last_login != 'N/A' else 'Не входил'),
        ]:
            value_label = QLabel(value)
            value_label.setStyleSheet("""
                font-weight: normal; 
                font-size: 13px; 
                color: #333; 
                padding: 8px; 
                background-color: white; 
                border-radius: 4px;
                border: 1px solid #E0E0E0;
            """)
            info_layout.addRow(f"  {label}:", value_label)
        scroll_layout.addWidget(info_group)

        # ─── Группа: Редактировать данные ────────────────────────
        edit_group = self._create_group_box("✏️ Редактировать данные")
        edit_layout = QFormLayout(edit_group)

        self.edit_full_name = QLineEdit(self.user_data.get('full_name', ''))
        self.edit_full_name.setPlaceholderText("Введите ФИО")
        self.edit_full_name.setMinimumHeight(40)
        self.edit_full_name.setStyleSheet(self._input_style())
        edit_layout.addRow("  ФИО:", self.edit_full_name)

        self.edit_email = QLineEdit(self.user_data.get('email', '') or '')
        self.edit_email.setPlaceholderText("Введите Email")
        self.edit_email.setMinimumHeight(40)
        self.edit_email.setStyleSheet(self._input_style())
        edit_layout.addRow("  Email:", self.edit_email)

        save_button = QPushButton("💾 Сохранить изменения")
        save_button.setFixedHeight(45)
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: #27AE60; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
            }} 
            QPushButton:hover {{ 
                background-color: #219653; 
            }}
            QPushButton:pressed {{ 
                background-color: #1E8449; 
            }}
        """)
        save_button.clicked.connect(self.save_profile_data)
        edit_layout.addRow(save_button)
        scroll_layout.addWidget(edit_group)

        # ─── Группа: Смена пароля ────────────────────────────────
        password_group = self._create_group_box("🔐 Смена пароля")
        password_layout = QFormLayout(password_group)

        self.password_new = QLineEdit()
        self.password_new.setPlaceholderText("Минимум 6 символов")
        self.password_new.setEchoMode(QLineEdit.Password)
        self.password_new.setMinimumHeight(40)
        self.password_new.setStyleSheet(self._input_style())
        password_layout.addRow("  Новый пароль:", self.password_new)

        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Повторите новый пароль")
        self.password_confirm.setEchoMode(QLineEdit.Password)
        self.password_confirm.setMinimumHeight(40)
        self.password_confirm.setStyleSheet(self._input_style())
        password_layout.addRow("  Повтор пароля:", self.password_confirm)

        change_password_button = QPushButton("🔑 Изменить пароль")
        change_password_button.setFixedHeight(45)
        change_password_button.setCursor(Qt.CursorShape.PointingHandCursor)
        change_password_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {self.PRIMARY_COLOR}; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
            }} 
            QPushButton:hover {{ 
                background-color: {self.PRIMARY_DARK}; 
            }}
            QPushButton:pressed {{ 
                background-color: #0a3a7a; 
            }}
        """)
        change_password_button.clicked.connect(self.change_password)
        password_layout.addRow(change_password_button)
        scroll_layout.addWidget(password_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        self.content_layout.addWidget(scroll, 1)
        main_layout.addWidget(self.content_widget)

    # ─── Вспомогательные методы ──────────────────────────────────
    
    def _create_group_box(self, title: str) -> QGroupBox:
        """Создаёт группу с единым стилем"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{ 
                font-weight: bold; 
                font-size: 14px; 
                color: {self.PRIMARY_COLOR}; 
                border: 2px solid {self.PRIMARY_COLOR}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 10px; 
            }} 
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px; 
            }}
        """)
        return group

    def _input_style(self) -> str:
        """Единый стиль для полей ввода"""
        return f"""
            QLineEdit {{ 
                background-color: white; 
                border: 1px solid #D0D0D0; 
                border-radius: 6px; 
                padding: 10px 14px; 
                font-size: 13px; 
                color: #222222; 
            }}
            QLineEdit:focus {{ 
                border: 2px solid {self.PRIMARY_COLOR}; 
                background-color: #FFFFFF; 
                outline: none; 
            }}
            QLineEdit::placeholder {{ 
                color: #BBBBBB; 
            }}
        """

    # ─── Обработчики событий ─────────────────────────────────────

    def go_back(self):
        self.back_to_table.emit()
        self.close()

    def logout(self):
        """Выход из аккаунта с возвратом на главный экран"""
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()

    def save_profile_data(self):
        """Сохранение изменённых данных профиля"""
        full_name = self.edit_full_name.text().strip()
        email = self.edit_email.text().strip()
        
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Поле ФИО не может быть пустым!")
            return
            
        # Валидация email если указан
        if email and '@' not in email:
            QMessageBox.warning(self, "Ошибка", "Введите корректный Email!")
            return
            
        try:
            update_data = {
                'full_name': full_name, 
                'email': email if email else None
            }
            self.db.update_record('users', self.user_data['id'], update_data)
            
            # Обновляем локальные данные
            self.user_data['full_name'] = full_name
            self.user_data['email'] = email if email else 'N/A'
            
            QMessageBox.information(
                self, 
                "✅ Успешно", 
                f"Данные обновлены!\n\nФИО: {full_name}\nEmail: {email if email else 'Не указан'}"
            )
            self.setWindowTitle(f"Личный кабинет | {full_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось обновить данные:\n{str(e)}")

    def change_password(self):
        """
        Смена пароля с валидацией как при регистрации
        """
        new_password = self.password_new.text().strip()
        confirm_password = self.password_confirm.text().strip()
        
        # Валидация 1: поля не пустые
        if not new_password or not confirm_password:
            QMessageBox.warning(self, "Ошибка", "Заполните оба поля пароля!")
            return
            
        # Валидация 2: длина пароля (как в регистрации)
        if len(new_password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов!")
            return
            
        # Валидация 3: совпадение паролей (как в регистрации)
        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return
            
        # Валидация 4: пароль не должен совпадать с текущим (опционально)
        # Можно добавить проверку, если храните хеш текущего пароля
        
        try:
            # Хешируем пароль тем же методом, что и при регистрации
            hashed_password = PasswordHelper.hash_password(new_password)
            
            # Обновляем пароль в БД
            # ВАЖНО: Убедитесь, что в Database есть метод update_user_password
            if hasattr(self.db, 'update_user_password'):
                self.db.update_user_password(self.user_data['id'], hashed_password)
            else:
                # Фолбэк: используем update_record
                self.db.update_record('users', self.user_data['id'], {'password_hash': hashed_password})
            
            # Очищаем поля
            self.password_new.clear()
            self.password_confirm.clear()
            
            QMessageBox.information(self, "✅ Успешно", "Пароль успешно изменён!\nТеперь используйте новый пароль для входа.")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось изменить пароль:\n{str(e)}")