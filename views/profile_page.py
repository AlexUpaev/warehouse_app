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

        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet("background-color: #F0F8FF; border-bottom: 2px solid #1A529C;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 20, 0)

        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setStyleSheet("QPushButton { background-color: transparent; color: #1A529C; border: none; border-radius: 4px; font-size: 24px; font-weight: bold; } QPushButton:hover { background-color: #E3F2FD; color: #0d47a1; }")
        top_layout.addWidget(self.menu_button)

        back_button = QPushButton("← Назад к таблицам")
        back_button.setFixedSize(180, 36)
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet("QPushButton { background-color: #1A529C; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 13px; } QPushButton:hover { background-color: #0d47a1; }")
        back_button.clicked.connect(self.go_back)
        top_layout.addWidget(back_button)

        title_label = QLabel(f"Личный кабинет: {self.user_data['full_name']}")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #004085;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        logout_button = QPushButton("Выйти")
        logout_button.setFixedSize(80, 32)
        logout_button.setStyleSheet("QPushButton { background-color: #6C757D; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #5A6268; }")
        logout_button.clicked.connect(self.logout)
        top_layout.addWidget(logout_button)

        self.content_layout.addWidget(top_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background-color: #FAFAFA;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #FAFAFA;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        scroll_layout.setSpacing(20)

        info_group = QGroupBox("📋 Информация о пользователе")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1A529C; border: 2px solid #1A529C; border-radius: 8px; margin-top: 12px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 8px; }")
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
            ("Статус", "Активен" if self.user_data.get('is_active') else "Неактивен"),
            ("Дата регистрации", created_at),
            ("Последний вход", last_login),
        ]:
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: normal; font-size: 13px; color: #333; padding: 8px; background-color: white; border-radius: 4px;")
            info_layout.addRow(f"  {label}:", value_label)
        scroll_layout.addWidget(info_group)

        edit_group = QGroupBox("✏️ Редактировать данные")
        edit_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1A529C; border: 2px solid #1A529C; border-radius: 8px; margin-top: 12px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 8px; }")
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
        save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #388E3C; }")
        save_button.clicked.connect(self.save_profile_data)
        edit_layout.addRow(save_button)
        scroll_layout.addWidget(edit_group)

        password_group = QGroupBox("🔐 Смена пароля")
        password_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1A529C; border: 2px solid #1A529C; border-radius: 8px; margin-top: 12px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 8px; }")
        password_layout = QFormLayout(password_group)

        self.password_new = QLineEdit()
        self.password_new.setPlaceholderText("Введите новый пароль")
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
        change_password_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #F57C00; }")
        change_password_button.clicked.connect(self.change_password)
        password_layout.addRow(change_password_button)
        scroll_layout.addWidget(password_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        self.content_layout.addWidget(scroll, 1)
        main_layout.addWidget(self.content_widget)

    def _input_style(self):
        return """
            QLineEdit { background-color: white; border: 1px solid #D0D0D0; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #222222; }
            QLineEdit:focus { border: 1px solid #1A529C; background-color: #FFFFFF; outline: none; }
        """

    def go_back(self):
        self.back_to_table.emit()
        self.close()

    def logout(self):
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()

    def save_profile_data(self):
        full_name = self.edit_full_name.text().strip()
        email = self.edit_email.text().strip()
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Поле ФИО не может быть пустым!")
            return
        try:
            update_data = {'full_name': full_name, 'email': email if email else None}
            self.db.update_record('users', self.user_data['id'], update_data)
            self.user_data['full_name'] = full_name
            self.user_data['email'] = email if email else 'N/A'
            QMessageBox.information(self, "Успешно", f"Данные обновлены!\n\nФИО: {full_name}\nEmail: {email if email else 'Не указан'}")
            self.setWindowTitle(f"Личный кабинет | {full_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные:\n{str(e)}")

    def change_password(self):
        new_password = self.password_new.text().strip()
        confirm_password = self.password_confirm.text().strip()
        if not new_password:
            QMessageBox.warning(self, "Ошибка", "Введите новый пароль!")
            return
        if len(new_password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов!")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return
        try:
            hashed_password = PasswordHelper.hash_password(new_password)
            self.db.update_user_password(self.user_data['id'], hashed_password)
            self.password_new.clear()
            self.password_confirm.clear()
            QMessageBox.information(self, "Успешно", "Пароль успешно изменён!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить пароль:\n{str(e)}")