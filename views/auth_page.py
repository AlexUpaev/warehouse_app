# auth_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QHBoxLayout, QMessageBox, QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from database import Database


class AuthPage(QWidget):
    switch_to_registration = Signal()
    login_successful = Signal(dict)

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.setup_styles()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)

        form_container = QFrame()
        form_container.setFixedWidth(400)
        form_container.setObjectName("formContainer")
        form_container.setStyleSheet("""
            QFrame#formContainer {
                background-color: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #E0E0E0;
                padding: 32px;
            }
        """)

        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(24)
        form_layout.setAlignment(Qt.AlignCenter)

        title = QLabel('Вход в систему')
        title.setFont(QFont('Segoe UI', 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")
        title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title)

        subtitle = QLabel('Введите данные для авторизации')
        subtitle.setFont(QFont('Segoe UI', 11))
        subtitle.setStyleSheet("color: #666666; margin-bottom: 24px;")
        subtitle.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(subtitle)

        login_container = QVBoxLayout()
        login_container.setSpacing(6)

        login_label = QLabel('Логин')
        login_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Medium))
        login_label.setStyleSheet("color: #333333;")

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText('Введите ваш логин')
        self.login_input.setMinimumHeight(44)
        self.login_input.setStyleSheet("""
            QLineEdit {
                background-color: #FAFAFA;
                border: 1px solid #D0D0D0;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                color: #222222;
                selection-background-color: #4A90E2;
            }
            QLineEdit:focus {
                border: 1px solid #4A90E2;
                background-color: #FFFFFF;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #AAAAAA;
                font-size: 14px;
            }
        """)

        login_container.addWidget(login_label)
        login_container.addWidget(self.login_input)
        form_layout.addLayout(login_container)

        password_container = QVBoxLayout()
        password_container.setSpacing(6)

        password_label = QLabel('Пароль')
        password_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Medium))
        password_label.setStyleSheet("color: #333333;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Введите ваш пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(44)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #FAFAFA;
                border: 1px solid #D0D0D0;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                color: #222222;
                selection-background-color: #4A90E2;
            }
            QLineEdit:focus {
                border: 1px solid #4A90E2;
                background-color: #FFFFFF;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #AAAAAA;
                font-size: 14px;
            }
        """)

        password_container.addWidget(password_label)
        password_container.addWidget(self.password_input)
        form_layout.addLayout(password_container)

        # Кнопка входа
        login_btn = QPushButton('Войти')
        login_btn.setMinimumHeight(46)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A529C;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                padding: 12px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #164786;
            }
            QPushButton:pressed {
                background-color: #123A6E;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        login_btn.clicked.connect(self.handle_login)
        form_layout.addWidget(login_btn)

        # Ссылка на регистрацию
        link_container = QHBoxLayout()
        link_container.setAlignment(Qt.AlignCenter)

        link_label = QLabel('Еще нет аккаунта?')
        link_label.setFont(QFont('Segoe UI', 10))
        link_label.setStyleSheet("color: #666666;")

        reg_link = QLabel('<a href="#" style="color: #1A529C; text-decoration: none; font-weight: 600;">Зарегистрироваться</a>')
        reg_link.setFont(QFont('Segoe UI', 10))
        reg_link.setTextFormat(Qt.TextFormat.RichText)
        reg_link.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        reg_link.linkActivated.connect(lambda: self.switch_to_registration.emit())
        reg_link.setStyleSheet("""
            QLabel:hover {
                text-decoration: underline;
            }
        """)

        link_container.addWidget(link_label)
        link_container.addWidget(reg_link)
        form_layout.addLayout(link_container)

        main_layout.addWidget(form_container)
        self.setLayout(main_layout)

    def setup_styles(self):
        self.setStyleSheet("QWidget { background-color: white; }")

    def handle_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return

        user = self.db.authenticate_user(login, password)

        if user:
            self.login_successful.emit(user)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')

    def clear_fields(self):
        self.login_input.clear()
        self.password_input.clear()
