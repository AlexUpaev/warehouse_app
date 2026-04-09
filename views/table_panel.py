import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QScrollArea, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QPoint, Signal, QPropertyAnimation, QEasingCurve, QModelIndex, QDate, QDateTime
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QValidator
from datetime import date, datetime
from database import Database
from dateutil import tz

TABLES = {
    "Пользователи": "users",
    "Категории": "categories",
    "Поставщики": "suppliers",
    "Материалы": "materials",
    "Транзакции": "transactions",
    "История изменений": "material_history"
}

HEADERS = {
    "users": ["ID", "Логин", "ФИО", "Email", "Роль", "Активен", "Создан", "Последний вход"],
    "categories": ["ID", "Название", "Описание", "Создана"],
    "suppliers": ["ID", "Название", "Контактное лицо", "Телефон", "Email", "Адрес", "Создан"],
    "materials": [
        "ID", "Наименование", "Количество", "Ед.", "Цена (₽)", "Мин. запас",
        "Поставщик", "Описание", "Категория", "Создал", "Создан", "Обновлен"
    ],
    "transactions": [
        "ID", "Материал", "Пользователь", "Количество", "Тип",
        "Документ", "Дата документа", "Примечание", "Создана"
    ],
    "material_history": [
        "ID", "Материал", "Было", "Стало", "Разница",
        "Действие", "Примечание", "Изменил", "Время"
    ]
}

COLUMN_MAPPING = {
    "users": {
        "ID": "id", "Логин": "login", "ФИО": "full_name", "Email": "email",
        "Роль": "role", "Активен": "is_active", "Создан": "created_at", "Последний вход": "last_login"
    },
    "categories": {
        "ID": "id", "Название": "name", "Описание": "description", "Создана": "created_at"
    },
    "suppliers": {
        "ID": "id", "Название": "name", "Контактное лицо": "contact_person",
        "Телефон": "phone", "Email": "email", "Адрес": "address", "Создан": "created_at"
    },
    "materials": {
        "ID": "id", "Наименование": "name", "Количество": "quantity", "Ед.": "unit",
        "Цена (₽)": "price", "Мин. запас": "min_quantity", "Поставщик": "supplier",
        "Описание": "description", "Категория": "category_name", "Создал": "created_by_name",
        "Создан": "created_at", "Обновлен": "updated_at"
    },
    "transactions": {
        "ID": "id", "Материал": "material_name", "Пользователь": "user_name",
        "Количество": "quantity", "Тип": "transaction_type", "Документ": "document_number",
        "Дата документа": "document_date", "Примечание": "notes", "Создана": "created_at"
    },
    "material_history": {
        "ID": "id", "Материал": "material_name", "Было": "old_quantity", "Стало": "new_quantity",
        "Разница": "difference", "Действие": "action_type", "Примечание": "notes",
        "Изменил": "changed_by_name", "Время": "changed_at"
    }
}

HIDDEN_FIELDS = {
    "users": ["ID", "Создан", "Последний вход"],
    "categories": ["ID", "Создана"],
    "suppliers": ["ID", "Создан"],
    "materials": ["ID", "Создал", "Создан", "Обновлен"],
    "transactions": ["ID", "Создана"],
    "material_history": ["ID", "Время"]
}

NUMERIC_COLUMNS = {
    "users": [0], "categories": [0], "suppliers": [0],
    "materials": [0, 2, 4, 5], "transactions": [0, 3], "material_history": [0, 2, 3, 4]
}

DATE_COLUMNS = {
    "users": [6, 7], "categories": [3], "suppliers": [6],
    "materials": [10, 11], "transactions": [6, 8], "material_history": [8]
}

MAX_CELL_LENGTH = 60

class PhoneValidator(QValidator):
    def validate(self, text, pos):
        if not text:
            return QValidator.Intermediate, text, pos
        digits = ''.join(filter(str.isdigit, text))
        if len(digits) > 11:
            return QValidator.Invalid, text, pos
        return QValidator.Intermediate, text, pos

class PriceValidator(QValidator):
    def validate(self, text, pos):
        if not text:
            return QValidator.Intermediate, text, pos
        try:
            float(text.replace(',', '.'))
            return QValidator.Acceptable, text, pos
        except ValueError:
            return QValidator.Invalid, text, pos

class InputForm(QDialog):
    def __init__(self, table_name, fields_or_values, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        form_layout = QFormLayout()
        self.setLayout(form_layout)
        
        if isinstance(fields_or_values, list):
            fields = fields_or_values
            values = None
        elif isinstance(fields_or_values, dict):
            fields = list(fields_or_values.keys())
            values = fields_or_values
        else:
            raise TypeError("Неподдерживаемый тип аргумента.")

        hidden = HIDDEN_FIELDS.get(table_name, [])
        fields = [f for f in fields if f not in hidden]
        
        if table_name == "users" and values is None:
            fields = [f for f in fields if f != "Пароль" and f != "Подтверждение пароля"]
            try:
                email_idx = fields.index("Email")
                fields.insert(email_idx + 1, "Пароль")
                fields.insert(email_idx + 2, "Подтверждение пароля")
            except ValueError:
                fields.extend(["Пароль", "Подтверждение пароля"])

        self.input_fields = {}
        placeholders = {
            "Логин": "Например: user123",
            "Пароль": "Минимум 6 символов",
            "Подтверждение пароля": "Повторите пароль",
            "ФИО": "Иванов Иван Иванович",
            "Email": "user@example.com",
            "Роль": "admin, manager или user",
            "Наименование": "Например: Саморез по дереву 4.2x75",
            "Количество": "Число, например: 100",
            "Ед.": "шт, кг, м, мешок и т.д.",
            "Цена (₽)": "Например: 1.50 или 1500",
            "Мин. запас": "Например: 50",
            "Поставщик": "ООО \"Название\"",
            "Описание": "Краткое описание товара",
            "Категория": "ID категории или название",
            "Название": "Например: Крепежные изделия",
            "Телефон": "+7 (999) 123-45-67",
            "Адрес": "г. Москва, ул. Примерная, д. 1",
            "Контактное лицо": "Иванов Иван",
            "Документ": "ПРИХ-001/2025",
            "Дата документа": "дд.мм.гггг",
            "Примечание": "Дополнительная информация",
            "Тип": "incoming, outgoing, adjustment",
            "Пользователь": "ID или ФИО пользователя",
            "Материал": "ID или название материала",
            "Действие": "add, remove, adjust, create, update",
            "Было": "Предыдущее количество",
            "Стало": "Новое количество",
            "Разница": "Разница (Стало - Было)",
            "Время": "дд.мм.гггг чч:мм",
            "Создан": "дд.мм.гггг чч:мм",
            "Обновлен": "дд.мм.гггг чч:мм",
            "Последний вход": "дд.мм.гггг чч:мм",
            "Активен": "True или False",
            "Создал": "ID пользователя",
            "Изменил": "ID пользователя"
        }

        masks = {
            "Телефон": "+7 (000) 000-00-00",
            "Дата документа": "00.00.0000",
        }

        for field in fields:
            label = QLabel(field)
            input_field = QLineEdit()
            
            if field in placeholders:
                input_field.setPlaceholderText(placeholders[field])
            
            if field in masks:
                input_field.setInputMask(masks[field])
            elif field == "Телефон":
                input_field.setValidator(PhoneValidator())
            elif field in ["Цена (₽)", "Было", "Стало", "Разница", "Количество", "Мин. запас"]:
                input_field.setValidator(PriceValidator())
            elif field in ["Пароль", "Подтверждение пароля"]:
                input_field.setEchoMode(QLineEdit.Password)
            
            if values:
                value = values[field]
                if value is not None:
                    if isinstance(value, (date, datetime)):
                        if isinstance(value, datetime) and value.tzinfo is not None:
                            local_tz = tz.tzlocal()
                            local_value = value.astimezone(local_tz)
                        else:
                            local_value = value
                        input_field.setText(local_value.strftime("%d.%m.%Y %H:%M"))
                    else:
                        input_field.setText(str(value))
            
            self.input_fields[field] = input_field
            form_layout.addRow(label, input_field)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_submit)
        button_box.rejected.connect(self.reject)
        form_layout.addRow(button_box)

    def validate_and_submit(self):
        if self.table_name == "users":
            password = self.input_fields.get("Пароль", QLineEdit()).text()
            confirm = self.input_fields.get("Подтверждение пароля", QLineEdit()).text()
            
            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
                return
            if password != confirm:
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return
            
            if "Подтверждение пароля" in self.input_fields:
                del self.input_fields["Подтверждение пароля"]
        
        self.accept()

class SortableHeaderView(QHeaderView):
    sortRequested = Signal(int, bool)
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.sort_column = -1
        self.sort_ascending = True
        self.setSectionsClickable(True)
        self.sectionClicked.connect(self.on_section_clicked)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
    def on_section_clicked(self, logical_index):
        if logical_index == 0: return
        if self.sort_column == logical_index:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = logical_index
            self.sort_ascending = True
        self.sortRequested.emit(logical_index, self.sort_ascending)
        self.viewport().update()

class CustomFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
    def set_search_text(self, text):
        self.search_text = text.strip().lower()
        self.invalidateFilter()
    def filterAcceptsRow(self, source_row, source_parent):
        if not self.search_text: return True
        source_model = self.sourceModel()
        if source_model is None: return True
        for column in range(source_model.columnCount()):
            index = source_model.index(source_row, column, source_parent)
            cell_value = str(source_model.data(index, Qt.DisplayRole) or "").lower()
            if self.search_text in cell_value: return True
        return False

class EditableItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, table_panel=None):
        super().__init__(parent)
        self.table_panel = table_panel
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if isinstance(editor, QLineEdit):
            editor.setText(str(value) if value is not None else "")
            
    def setModelData(self, editor, model, index):
        if isinstance(editor, QLineEdit):
            new_value = editor.text()
            old_value = model.data(index, Qt.DisplayRole)
            
            if str(new_value) != str(old_value):
                reply = QMessageBox.question(
                    self.table_panel,
                    "Подтверждение изменения",
                    "Желаете изменить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    model.setData(index, new_value, Qt.EditRole)
                    if self.table_panel:
                        self.table_panel.save_cell_change(index, old_value, new_value)
                else:
                    editor.setText(str(old_value))

class SideMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedWidth(280)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("QWidget { background-color: #1A529C; color: white; }")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #0d47a1;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        menu_title = QLabel("Меню")
        menu_title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        header_layout.addWidget(menu_title)
        main_layout.addWidget(header)
        
        self.buttons_container = QWidget()
        self.buttons_container.setStyleSheet("background-color: transparent;")
        buttons_layout = QVBoxLayout(self.buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        
        menu_items = [
            ("👤 Личный кабинет", self.open_profile),
            ("📥 Приход/расход материала", self.open_materials_flow),
            ("📊 Отчёты по стройкам", self.open_reports),
        ]
        for icon_text, callback in menu_items:
            btn = self.create_menu_button(icon_text, callback)
            buttons_layout.addWidget(btn)
        buttons_layout.addStretch()
        main_layout.addWidget(self.buttons_container)
    
    def create_menu_button(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedHeight(55)
        btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: white; 
                text-align: left; 
                padding-left: 30px; 
                font-size: 14px; 
                font-weight: 500; 
                border: none; 
                border-left: 4px solid transparent; 
            }
            QPushButton:hover { 
                background-color: #1565C0; 
                border-left: 4px solid #64B5F6; 
            }
            QPushButton:pressed { 
                background-color: #0d47a1; 
            }
        """)
        btn.clicked.connect(callback)
        return btn
    
    def open_profile(self):
        if hasattr(self.parent_window, 'close_menu'): self.parent_window.close_menu()
        try:
            from .profile_page import ProfilePage
            self.profile_window = ProfilePage(self.parent_window.user_data)
            self.profile_window.back_to_table.connect(self.parent_window.show)
            self.profile_window.show()
            self.parent_window.hide()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть профиль:\n{str(e)}")
    
    def open_materials_flow(self):
        if hasattr(self.parent_window, 'close_menu'): self.parent_window.close_menu()
        QMessageBox.information(self, "Приход/расход материала", "Страница находится в разработке")
    
    def open_reports(self):
        if hasattr(self.parent_window, 'close_menu'): self.parent_window.close_menu()
        QMessageBox.information(self, "Отчёты по стройкам", "Страница находится в разработке")

class TablePanel(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.current_table_name = None
        self.menu_opened = False
        self.pending_changes = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Управление складом | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(1024, 768)

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
        self.menu_button.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: #1A529C; 
                border: none; 
                border-radius: 4px; 
                font-size: 24px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #E3F2FD; 
                color: #0d47a1; 
            } 
        """)
        self.menu_button.clicked.connect(self.toggle_menu)
        top_layout.addWidget(self.menu_button)

        user_label = QLabel(f"Пользователь: {self.user_data['full_name']} ({self.user_data['role']})")
        user_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        user_label.setStyleSheet("color: #004085;")
        top_layout.addWidget(user_label)

        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        self.table_selector = QComboBox()
        self.table_selector.addItems(TABLES.keys())
        self.table_selector.currentTextChanged.connect(self.load_table)
        buttons_layout.addWidget(self.table_selector)

        add_button = QPushButton("➕ Добавить")
        add_button.setFixedSize(120, 32)
        add_button.setStyleSheet("""
            QPushButton { 
                background-color: #007BFF; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
                font-size: 13px;
            } 
            QPushButton:hover { 
                background-color: #0056B3; 
            }
        """)
        add_button.clicked.connect(self.open_add_form)
        buttons_layout.addWidget(add_button)

        delete_button = QPushButton("🗑️ Удалить")
        delete_button.setFixedSize(100, 32)
        delete_button.setStyleSheet("""
            QPushButton { 
                background-color: #D32F2F; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
                font-size: 13px;
            } 
            QPushButton:hover { 
                background-color: #B71C1C; 
            }
        """)
        delete_button.clicked.connect(self.delete_selected_row)
        buttons_layout.addWidget(delete_button)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск...")
        self.search_bar.setFixedWidth(200)
        buttons_layout.addWidget(self.search_bar)

        self.search_button = QPushButton("🔍 Поиск")
        self.search_button.setFixedSize(90, 32)
        self.search_button.setStyleSheet("""
            QPushButton { 
                background-color: #17A2B8; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
                font-size: 13px;
            } 
            QPushButton:hover { 
                background-color: #138496; 
            }
        """)
        self.search_button.clicked.connect(self.perform_search)
        self.search_bar.returnPressed.connect(self.perform_search)
        buttons_layout.addWidget(self.search_button)

        logout_button = QPushButton("Выйти")
        logout_button.setFixedSize(80, 32)
        logout_button.setStyleSheet("""
            QPushButton { 
                background-color: #6C757D; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
                font-size: 13px;
            } 
            QPushButton:hover { 
                background-color: #5A6268; 
            }
        """)
        logout_button.clicked.connect(self.logout)
        buttons_layout.addWidget(logout_button)

        top_layout.addWidget(buttons_container)
        top_layout.addStretch()
        self.content_layout.addWidget(top_panel)

        self.data_table = QTableView()
        self.data_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setSortingEnabled(False)
        self.data_table.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.EditKeyPressed)
        
        header = SortableHeaderView(Qt.Horizontal, self.data_table)
        self.data_table.setHorizontalHeader(header)
        header.sortRequested.connect(self.sort_by_column)
        
        self.data_table.setStyleSheet("""
            QTableView { 
                background-color: white; 
                color: black; 
                font-size: 12px; 
                alternate-background-color: #fafafa;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section { 
                background-color: #004085; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 6px; 
                border: none; 
            }
            QHeaderView::section:hover { 
                background-color: #0056B3; 
            }
            QHeaderView::section:pressed { 
                background-color: #003366; 
            }
        """)
        
        delegate = EditableItemDelegate(self.data_table, self)
        self.data_table.setItemDelegate(delegate)
        
        self.content_layout.addWidget(self.data_table, 1)

        self.proxy_model = CustomFilterProxyModel()
        self.proxy_model.setSourceModel(None)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setDynamicSortFilter(False)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(40)
        bottom_panel.setStyleSheet("background-color: #F5F5F5; border-top: 1px solid #E0E0E0;")
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(15, 0, 15, 0)
        version_label = QLabel("Склад материалов v1.0 | PUTEVI")
        bottom_layout.addWidget(version_label)
        bottom_layout.addStretch()
        self.content_layout.addWidget(bottom_panel)

        main_layout.addWidget(self.content_widget)

        self.side_menu = SideMenu(self)
        self.side_menu.setParent(self)
        self.side_menu.setGeometry(-280, 0, 280, self.height())
        self.side_menu.show()
        
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.hide()
        self.overlay.mousePressEvent = lambda e: self.toggle_menu()
        self.side_menu.raise_()

        self.load_table("Пользователи")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'side_menu'): self.side_menu.setGeometry(-280, 0, 280, self.height())
        if hasattr(self, 'overlay'): self.overlay.setGeometry(0, 0, self.width(), self.height())
        self._adjust_column_widths()

    def toggle_menu(self):
        if self.menu_opened: self.close_menu()
        else: self.open_menu()

    def open_menu(self):
        self.overlay.show()
        self.overlay.raise_()
        self.side_menu.raise_()
        self.menu_opened = True
        self.menu_animation = QPropertyAnimation(self.side_menu, b"pos")
        self.menu_animation.setDuration(300)
        self.menu_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.menu_animation.setStartValue(QPoint(-280, 0))
        self.menu_animation.setEndValue(QPoint(0, 0))
        self.menu_animation.start()

    def close_menu(self):
        self.menu_animation = QPropertyAnimation(self.side_menu, b"pos")
        self.menu_animation.setDuration(300)
        self.menu_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.menu_animation.setStartValue(QPoint(0, 0))
        self.menu_animation.setEndValue(QPoint(-280, 0))
        self.menu_animation.finished.connect(self.on_menu_closed)
        self.menu_animation.start()

    def on_menu_closed(self):
        self.overlay.hide()
        self.menu_opened = False

    def perform_search(self):
        text = self.search_bar.text()
        self.proxy_model.set_search_text(text)

    def logout(self):
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()

    def sort_by_column(self, logical_index, ascending):
        table_name = TABLES[self.table_selector.currentText()]
        is_numeric = logical_index in NUMERIC_COLUMNS.get(table_name, [])
        is_date = logical_index in DATE_COLUMNS.get(table_name, [])
        sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder
        
        if is_numeric:
            self.proxy_model.setSortRole(Qt.EditRole)
        elif is_date:
            self.proxy_model.setSortRole(Qt.UserRole)
        else:
            self.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)
            self.proxy_model.setSortRole(Qt.DisplayRole)
            
        self.proxy_model.sort(logical_index, sort_order)
        if isinstance(self.data_table.horizontalHeader(), SortableHeaderView):
            header = self.data_table.horizontalHeader()
            header.sort_column = logical_index
            header.sort_ascending = ascending

    def reset_sort(self):
        self.proxy_model.sort(-1, Qt.AscendingOrder)

    def _adjust_column_widths(self):
        header = self.data_table.horizontalHeader()
        if not header or header.count() == 0:
            return
        
        for i in range(header.count()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        total_width = sum(header.sectionSize(i) for i in range(header.count()))
        viewport_width = self.data_table.viewport().width()
        
        if total_width < viewport_width:
            header.setSectionResizeMode(header.count() - 1, QHeaderView.ResizeMode.Stretch)

    def open_add_form(self):
        selected_table = TABLES[self.table_selector.currentText()]
        dialog = InputForm(selected_table, HEADERS[selected_table])
        if dialog.exec() == QDialog.Accepted:
            rus_data = {field: dialog.input_fields[field].text() for field in dialog.input_fields}
            eng_data = {}
            mapping = COLUMN_MAPPING.get(selected_table, {})

            for rus_key, value in rus_data.items():
                if rus_key in HIDDEN_FIELDS.get(selected_table, []):
                    continue

                eng_key = mapping.get(rus_key, rus_key.lower().replace(" ", "_"))

                if rus_key == "Пароль":
                    from utils.password_helper import PasswordHelper
                    eng_data['password_hash'] = PasswordHelper.hash_password(value)
                elif rus_key == "Активен":
                    eng_data[eng_key] = value.strip().lower() in ('true', '1', 'да', 'yes')
                elif not value or value.strip() == '':
                    eng_data[eng_key] = None
                else:
                    if rus_key in ["Количество", "Мин. запас"]:
                        try: eng_data[eng_key] = int(value)
                        except: eng_data[eng_key] = value
                    elif rus_key == "Цена (₽)":
                        try: eng_data[eng_key] = float(value.replace(',', '.'))
                        except: eng_data[eng_key] = value
                    else:
                        eng_data[eng_key] = value

            try:
                self.db.insert_record(selected_table, eng_data)
                QMessageBox.information(self, "Успешно", "Запись добавлена!")
                self.reload_current_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись:\n{str(e)}")

    def save_cell_change(self, index, old_value, new_value):
        row = index.row()
        col = index.column()
        table_name = TABLES[self.table_selector.currentText()]
        model = self.data_table.model()
        
        record_id = model.index(row, 0).data()
        header_name = HEADERS[table_name][col]
        db_column = COLUMN_MAPPING[table_name].get(header_name, header_name.lower().replace(" ", "_"))
        
        if header_name in ["Количество", "Мин. запас", "ID"]:
            try: new_value = int(new_value)
            except: pass
        elif header_name == "Цена (₽)":
            try: new_value = float(str(new_value).replace(',', '.'))
            except: pass
        elif header_name == "Активен":
            new_value = str(new_value).lower() in ('true', '1', 'да', 'yes')

        try:
            updated_data = {db_column: new_value}
            self.db.update_record(table_name, record_id, updated_data)
            QMessageBox.information(self, "Успешно", "Изменения сохранены в базе данных!")
            self.reload_current_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
            model.setData(index, old_value, Qt.DisplayRole)

    def delete_selected_row(self):
        selected_indexes = self.data_table.selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            model = self.data_table.model()
            record_id = model.index(row, 0).data()
            table_name = TABLES[self.table_selector.currentText()]
            
            try:
                dependencies = self.db.get_foreign_key_dependencies(table_name, record_id)
                
                if dependencies:
                    dep_text = "\n".join([f"• {table}: {count} записей" for table, count in dependencies.items()])
                    total = sum(dependencies.values())
                    
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Question)
                    msg.setWindowTitle("Подтверждение каскадного удаления")
                    msg.setText(f"Будет удалено {total} связанных записей:")
                    msg.setInformativeText(f"{dep_text}\n\nЖелаете продолжить?")
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg.setDefaultButton(QMessageBox.No)
                    
                    result = msg.exec()
                    
                    if result == QMessageBox.Yes:
                        deleted = self.db.cascade_delete(table_name, record_id)
                        deleted_text = "\n".join([f"• {table}: {count}" for table, count in deleted.items()])
                        total_deleted = sum(deleted.values())
                        QMessageBox.information(self, "Успешно", f"Удалено записей: {total_deleted}\n\n{deleted_text}")
                        self.reload_current_table()
                else:
                    confirm_result = QMessageBox.question(self, "Подтверждение удаления",
                                                       "Вы действительно хотите удалить выбранную запись?",
                                                       QMessageBox.Yes | QMessageBox.No)
                    if confirm_result == QMessageBox.Yes:
                        self.db.delete_record(table_name, record_id)
                        self.reload_current_table()
                        QMessageBox.information(self, "Успешно", "Запись успешно удалена!")
                        
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении:\n{str(e)}")
        else:
            QMessageBox.information(self, "Внимание", "Выберите запись для удаления.")

    def reload_current_table(self):
        self.load_table(self.table_selector.currentText())

    def load_table(self, display_name: str):
        table_name = TABLES[display_name]
        self.current_table_name = table_name
        try:
            rows = self.db.get_table_data(table_name)
            headers = HEADERS[table_name]
            model = QStandardItemModel(len(rows), len(headers))
            model.setHorizontalHeaderLabels(headers)

            for row_idx, row in enumerate(rows):
                row_values = list(row.values())
                for col_idx in range(len(headers)):
                    value = row_values[col_idx] if col_idx < len(row_values) else None
                    
                    item = QStandardItem()
                    
                    # ✅ ПРОСТОЙ И НАДЁЖНЫЙ ПОДХОД
                    if value is None:
                        display_text = ""
                    elif isinstance(value, datetime):
                        if value.tzinfo is not None:
                            local_value = value.astimezone(tz.tzlocal())
                        else:
                            local_value = value
                        display_text = local_value.strftime("%d.%m.%Y %H:%M")
                    elif isinstance(value, date):
                        display_text = value.strftime("%d.%m.%Y")
                    elif isinstance(value, bool):
                        display_text = "true" if value else "false"
                    else:
                        text = str(value)
                        if len(text) > MAX_CELL_LENGTH:
                            text = text[:MAX_CELL_LENGTH - 1] + "…"
                        display_text = text
                    
                    # ✅ УСТАНАВЛИВАЕМ ТЕКСТ И ДАННЫЕ
                    item.setText(display_text)
                    item.setData(display_text, Qt.ItemDataRole.DisplayRole)
                    item.setData(display_text, Qt.ItemDataRole.EditRole)
                    
                    # Выравнивание для чисел
                    if isinstance(value, (int, float)):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    
                    model.setItem(row_idx, col_idx, item)

            header = self.data_table.horizontalHeader()
            self._adjust_column_widths()

            self.proxy_model.setSourceModel(model)
            self.data_table.setModel(self.proxy_model)
            
            if isinstance(header, SortableHeaderView):
                header.sort_column = -1
                header.sort_ascending = True
            
            self.search_bar.clear()
            self.proxy_model.set_search_text("")
            self.reset_sort()

        except Exception as e:
            print(f"❌ Ошибка при загрузке таблицы '{table_name}': {e}")
            import traceback
            traceback.print_exc()
            error_model = QStandardItemModel(1, 1)
            error_model.setHorizontalHeaderLabels(["Ошибка"])
            error_model.setItem(0, 0, QStandardItem(str(e)))
            self.proxy_model.setSourceModel(error_model)
            self.data_table.setModel(self.proxy_model)