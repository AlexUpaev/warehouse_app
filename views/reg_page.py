# reg_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QHBoxLayout, QMessageBox, QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from database import Database


class RegPage(QWidget):
    switch_to_auth = Signal()
    registration_successful = Signal()

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.setup_styles()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30) 
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)

        form_container = QFrame()
        form_container.setFixedWidth(380)  
        form_container.setObjectName("formContainer")
        form_container.setStyleSheet("""
            QFrame#formContainer {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                padding: 20px;  /* ← Уменьшили внутренний padding */
            }
        """)

        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(16)  
        form_layout.setAlignment(Qt.AlignCenter)

        title = QLabel('Регистрация')
        title.setFont(QFont('Segoe UI', 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #222222;")
        title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title)

        subtitle = QLabel('Создайте новый аккаунт')
        subtitle.setFont(QFont('Segoe UI', 10))
        subtitle.setStyleSheet("color: #888888; margin-bottom: 4px;")  
        subtitle.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(subtitle)

        for field_name, placeholder, is_password, attr_name in [
            ('Логин', 'Придумайте уникальный логин', False, 'login_input'),
            ('ФИО', 'Иванов Иван Иванович', False, 'name_input'),
            ('Email (необязательно)', 'user@example.com', False, 'email_input'),
            ('Пароль', 'Минимум 6 символов', True, 'password_input'),
            ('Подтверждение пароля', 'Повторите пароль', True, 'confirm_input'),
        ]:
            container = QVBoxLayout()
            container.setSpacing(6) 

            label = QLabel(field_name)
            label.setFont(QFont('Segoe UI', 10, QFont.Weight.Medium))
            label.setStyleSheet("color: #444444;")

            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            if is_password:
                line_edit.setEchoMode(QLineEdit.Password)
            line_edit.setMinimumHeight(36)  
            line_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #DDDDDD;
                    border-radius: 6px;
                    padding: 6px 10px;  /* ← Уменьшили padding */
                    font-size: 13px;
                    color: #222222;
                }
                QLineEdit:focus {
                    border: 1px solid #1A529C;
                    outline: none;
                }
                QLineEdit::placeholder {
                    color: #BBBBBB;
                    font-size: 13px;
                }
            """)

            setattr(self, attr_name, line_edit)
            container.addWidget(label)
            container.addWidget(line_edit)
            form_layout.addLayout(container)

        reg_btn = QPushButton('Зарегистрироваться')
        reg_btn.setMinimumHeight(44)
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
                margin-top: 12px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        reg_btn.clicked.connect(self.handle_registration)
        form_layout.addWidget(reg_btn)

        link_container = QHBoxLayout()
        link_container.setAlignment(Qt.AlignCenter)

        link_label = QLabel('Уже есть аккаунт?')
        link_label.setFont(QFont('Segoe UI', 10))
        link_label.setStyleSheet("color: #888888;")

        auth_link = QLabel('<a href="#" style="color: #1A529C; text-decoration: none; font-weight: 600;">Войти</a>')
        auth_link.setFont(QFont('Segoe UI', 10))
        auth_link.setTextFormat(Qt.TextFormat.RichText)
        auth_link.setCursor(Qt.CursorShape.PointingHandCursor)
        auth_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        auth_link.linkActivated.connect(lambda: self.switch_to_auth.emit())
        auth_link.setStyleSheet("""
            QLabel:hover {
                text-decoration: underline;
            }
        """)

        link_container.addWidget(link_label)
        link_container.addWidget(auth_link)
        form_layout.addLayout(link_container)

        main_layout.addWidget(form_container)
        self.setLayout(main_layout)

    def setup_styles(self):
        self.setStyleSheet("QWidget { background-color: white; }")

    def handle_registration(self):
        login = self.login_input.text().strip()
        full_name = self.name_input.text().strip()
        email = self.email_input.text().strip() or None
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        errors = []
        if not login:
            errors.append('Введите логин')
        if not full_name:
            errors.append('Введите ФИО')
        if not password:
            errors.append('Введите пароль')
        if password != confirm:
            errors.append('Пароли не совпадают')
        if len(password) < 6:
            errors.append('Пароль должен быть не менее 6 символов')
        if login and self.db.check_login_exists(login):
            errors.append('Этот логин уже занят')

        if errors:
            QMessageBox.warning(self, 'Ошибка', '\n'.join(errors))
            return

        success = self.db.register_user(login=login, password=password, full_name=full_name, email=email)
        if success:
            self.registration_successful.emit()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось зарегистрировать пользователя')

    def clear_fields(self):
        self.login_input.clear()
        self.name_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
