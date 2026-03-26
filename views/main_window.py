# main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QStackedWidget
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from database import Database
from config import Config
from .auth_page import AuthPage
from .reg_page import RegPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Склад материалов | PUTEVI")
        self.setGeometry(100, 100, 700, 500)
        self.setMinimumSize(600, 450)
        
        self.database = Database()
        self.config = Config()
        self.current_user = None
        
        self.setup_ui()
        self.load_logo()
        self.init_forms()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.create_top_panel(main_layout)
        self.create_center_area(main_layout)
        self.create_bottom_panel(main_layout)
    
    def create_top_panel(self, parent_layout):
        top_frame = QFrame()
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F8FF;
                border-bottom: 2px solid #1A529C;
            }
        """)
        top_frame.setFixedHeight(130)
        
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 15, 20, 15)
        top_layout.setSpacing(20)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(40, 40)
        left_layout.addWidget(self.logo_label)
        
        title_label = QLabel("Подключение к базе данных")
        title_label.setStyleSheet("""
            color: #1A529C;
            font-weight: bold;
            font-size: 14px;
        """)
        left_layout.addWidget(title_label)
        
        top_layout.addLayout(left_layout)
        top_layout.addStretch(1)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        
        self.status_label = QLabel("Подключение к БД")
        self.status_label.setStyleSheet("""
            color: #333333;
            font-size: 12px;
        """)
        right_layout.addWidget(self.status_label)
        
        self.test_btn = QPushButton("Проверить подключение")
        self.test_btn.setFixedSize(180, 35)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A529C;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d47a1;
            }
        """)
        self.test_btn.clicked.connect(self.test_connection)
        right_layout.addWidget(self.test_btn)
        
        self.result_label = QLabel("---")
        self.result_label.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-family: Consolas;
        """)
        right_layout.addWidget(self.result_label)
        
        top_layout.addLayout(right_layout)
        parent_layout.addWidget(top_frame)
    
    def create_center_area(self, parent_layout):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white;")
        self.create_welcome_page()
        parent_layout.addWidget(self.stacked_widget, 1)
    
    def create_welcome_page(self):
        welcome_widget = QWidget()
        welcome_widget.setStyleSheet("background-color: white;")
        
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(40, 40, 40, 40)
        welcome_layout.setSpacing(0)
        
        welcome_label = QLabel("Добро пожаловать!")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            color: #1A529C;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 30px;
        """)
        welcome_layout.addWidget(welcome_label)
        
        info_label = QLabel("Для работы с системой необходимо подключиться к базе данных PostgreSQL")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            color: #666666;
            font-size: 14px;
            margin-bottom: 50px;
        """)
        welcome_layout.addWidget(info_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.addStretch(1)
        
        self.auth_btn = QPushButton("Авторизация")
        self.auth_btn.setFixedSize(140, 40)
        self.auth_btn.setEnabled(False)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A529C;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.auth_btn.clicked.connect(self.show_auth_page)
        buttons_layout.addWidget(self.auth_btn)
        
        self.reg_btn = QPushButton("Регистрация")
        self.reg_btn.setFixedSize(140, 40)
        self.reg_btn.setEnabled(False)
        self.reg_btn.setStyleSheet("""
            QPushButton {
                background-color: #388E3C;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.reg_btn.clicked.connect(self.show_reg_page)
        buttons_layout.addWidget(self.reg_btn)
        
        buttons_layout.addStretch(1)
        welcome_layout.addLayout(buttons_layout)
        welcome_layout.addStretch(1)
        self.stacked_widget.addWidget(welcome_widget)
    
    def create_bottom_panel(self, parent_layout):
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(50)
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-top: 1px solid #E0E0E0;
            }
        """)
        
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(15, 0, 15, 0)
        
        version_label = QLabel("Склад материалов v1.0 | PUTEVI")
        version_label.setStyleSheet("color: #616161;")
        bottom_layout.addWidget(version_label)
        bottom_layout.addStretch(1)
        
        exit_btn = QPushButton("Выход")
        exit_btn.setFixedSize(90, 32)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(exit_btn)
        parent_layout.addWidget(bottom_frame)
    
    def init_forms(self):
        self.auth_page = AuthPage()
        self.reg_page = RegPage()
        
        self.stacked_widget.addWidget(self.auth_page)
        self.stacked_widget.addWidget(self.reg_page)
        
        self.auth_page.switch_to_registration.connect(self.show_reg_page)
        self.auth_page.login_successful.connect(self.on_login_success)
        self.reg_page.switch_to_auth.connect(self.show_auth_page)
        self.reg_page.registration_successful.connect(self.on_registration_success)
    
    def load_logo(self):
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'logo.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaled(40, 40, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation))
    
    def test_connection(self):
        """Проверка подключения к PostgreSQL"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            conn.close()

            self.result_label.setText("✅ PostgreSQL подключён")
            self.status_label.setText(f"Подключено: {db_version[0][:30]}...")
            self.auth_btn.setEnabled(True)
            self.reg_btn.setEnabled(True)

            QMessageBox.information(self, "Успех", 
                "Подключение к базе данных установлено!\n"
                "Теперь вы можете авторизоваться или зарегистрироваться.")

        except Exception as e:
            error_msg = str(e)
            self.result_label.setText(f"❌ Ошибка: {error_msg[:50]}...")
            self.status_label.setText("Ошибка подключения")
            QMessageBox.warning(self, "Ошибка", 
                f"Не удалось подключиться к PostgreSQL:\n{error_msg}")
    
    def show_auth_page(self):
        """Показывает страницу авторизации"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", 
                "Нет подключения к базе данных.\n"
                "Нажмите 'Проверить подключение'.")
            return

        self.stacked_widget.setCurrentWidget(self.auth_page)
        self.auth_page.clear_fields()
    
    def show_reg_page(self):
        """Показывает страницу регистрации"""
        self.stacked_widget.setCurrentWidget(self.reg_page)
        self.reg_page.clear_fields()
    
    def show_welcome_page(self):
        self.stacked_widget.setCurrentIndex(0)
    
    def on_login_success(self, user_data):
        self.current_user = user_data
        self.close()
        from .table_panel import TablePanel
        self.table_window = TablePanel(user_data)
        self.table_window.show()
    
    def on_registration_success(self):
        self.show_auth_page()
        QMessageBox.information(self, 'Успешная регистрация', 
                               'Регистрация завершена успешно!\n'
                               'Теперь вы можете войти в систему.')
        self.auth_btn.setEnabled(True)
