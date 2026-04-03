import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QScrollArea
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QPoint, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem
from datetime import date, datetime
from database import Database

# Глобальные переменные и структуры
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

# Столбцы с числовыми данными (для правильной сортировки)
NUMERIC_COLUMNS = {
    "users": [0],
    "categories": [0],
    "suppliers": [0],
    "materials": [0, 2, 4, 5],
    "transactions": [0, 3],
    "material_history": [0, 2, 3, 4]
}

# Столбцы с датами
DATE_COLUMNS = {
    "users": [6, 7],
    "categories": [3],
    "suppliers": [6],
    "materials": [10, 11],
    "transactions": [6, 8],
    "material_history": [8]
}

MAX_CELL_LENGTH = 60


class InputForm(QDialog):
    def __init__(self, fields_or_values, parent=None):
        super().__init__(parent)
        form_layout = QFormLayout()
        self.setLayout(form_layout)

        if isinstance(fields_or_values, list):
            fields = fields_or_values
            values = None
        elif isinstance(fields_or_values, dict):
            fields = list(fields_or_values.keys())
            values = fields_or_values
        else:
            raise TypeError("Неподдерживаемый тип аргумента для формы.")

        self.input_fields = {}
        for i, field in enumerate(fields):
            label = QLabel(field)
            input_field = QLineEdit()
            if values:
                input_field.setText(str(values[field]))
            self.input_fields[field] = input_field
            form_layout.addRow(label, input_field)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_submit)
        button_box.rejected.connect(self.reject)
        form_layout.addRow(button_box)

    def validate_and_submit(self):
        valid = all(self.input_fields[field].text() != '' for field in self.input_fields)
        if valid:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Необходимо заполнить все поля.")


class SortableHeaderView(QHeaderView):
    """Заголовок таблицы с сортировкой при клике."""
    
    sortRequested = Signal(int, bool)
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.sort_column = -1
        self.sort_ascending = True
        self.setSectionsClickable(True)
        self.sectionClicked.connect(self.on_section_clicked)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
    def on_section_clicked(self, logical_index):
        if logical_index == 0:
            return
        
        if self.sort_column == logical_index:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = logical_index
            self.sort_ascending = True
        
        self.sortRequested.emit(logical_index, self.sort_ascending)
        self.viewport().update()


class CustomFilterProxyModel(QSortFilterProxyModel):
    """Прокси-модель с поиском по полному совпадению в любой ячейке."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
    
    def set_search_text(self, text):
        self.search_text = text.strip().lower()
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row, source_parent):
        if not self.search_text:
            return True
        
        source_model = self.sourceModel()
        if source_model is None:
            return True
        
        for column in range(source_model.columnCount()):
            index = source_model.index(source_row, column, source_parent)
            cell_value = str(source_model.data(index, Qt.DisplayRole) or "").lower()
            
            if cell_value == self.search_text:
                return True
        
        return False


class SideMenu(QWidget):
    """Боковое меню с плавной анимацией."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedWidth(280)
        self.setVisible(False)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1A529C;
                color: white;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Заголовок меню
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #0d47a1;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        menu_title = QLabel("Меню")
        menu_title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        menu_title.setStyleSheet("color: white;")
        header_layout.addWidget(menu_title)
        
        main_layout.addWidget(header)
        
        # Контейнер для кнопок меню
        self.buttons_container = QWidget()
        self.buttons_container.setStyleSheet("background-color: transparent;")
        buttons_layout = QVBoxLayout(self.buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        
        # ПУНКТЫ МЕНЮ
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
        """Создаёт кнопку меню."""
        btn = QPushButton(text)
        btn.setFixedHeight(55)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        """Открывает страницу личного кабинета."""
        if hasattr(self.parent_window, 'close_menu'):
            self.parent_window.close_menu()
        
        try:
            from .profile_page import ProfilePage
            self.profile_window = ProfilePage(self.parent_window.user_data)
            self.profile_window.back_to_table.connect(self.parent_window.show)
            self.profile_window.show()
            self.parent_window.hide()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть профиль:\n{str(e)}")
    
    def open_materials_flow(self):
        """Заглушка для страницы прихода/расхода."""
        if hasattr(self.parent_window, 'close_menu'):
            self.parent_window.close_menu()
        
        QMessageBox.information(self, "Приход/расход материала", 
            "Страница находится в разработке\n\n"
            "Здесь будет:\n"
            "- Оформление прихода материалов\n"
            "- Оформление расхода\n"
            "- История операций")
    
    def open_reports(self):
        """Заглушка для страницы отчётов."""
        if hasattr(self.parent_window, 'close_menu'):
            self.parent_window.close_menu()
        
        QMessageBox.information(self, "Отчёты по стройкам", 
            "Страница находится в разработке\n\n"
            "Здесь будет:\n"
            "- Отчёты по объектам\n"
            "- Статистика использования\n"
            "- Экспорт данных")


class TablePanel(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.current_table_name = None
        self.menu_opened = False
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

        # Контейнер для основного контента
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Верхняя панель
        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet("background-color: #F0F8FF; border-bottom: 2px solid #1A529C;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 20, 0)

        # КНОПКА-ГАМБУРГЕР
        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
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

        add_button = QPushButton("Добавить")
        add_button.setFixedSize(100, 32)
        add_button.setStyleSheet("QPushButton { background-color: #007BFF; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #0056B3; }")
        add_button.clicked.connect(self.open_add_form)
        buttons_layout.addWidget(add_button)

        edit_button = QPushButton("Редактировать")
        edit_button.setFixedSize(100, 32)
        edit_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #388E3C; }")
        edit_button.clicked.connect(self.edit_selected_row)
        buttons_layout.addWidget(edit_button)

        delete_button = QPushButton("Удалить")
        delete_button.setFixedSize(100, 32)
        delete_button.setStyleSheet("QPushButton { background-color: #D32F2F; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #B71C1C; }")
        delete_button.clicked.connect(self.delete_selected_row)
        buttons_layout.addWidget(delete_button)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск (полное совпадение)...")
        self.search_bar.setFixedWidth(200)
        buttons_layout.addWidget(self.search_bar)

        self.search_button = QPushButton("Поиск")
        self.search_button.setFixedSize(80, 32)
        self.search_button.setStyleSheet("QPushButton { background-color: #17A2B8; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #138496; }")
        self.search_button.clicked.connect(self.perform_search)
        self.search_bar.returnPressed.connect(self.perform_search)
        buttons_layout.addWidget(self.search_button)

        logout_button = QPushButton("Выйти")
        logout_button.setFixedSize(80, 32)
        logout_button.setStyleSheet("QPushButton { background-color: #6C757D; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #5A6268; }")
        logout_button.clicked.connect(self.logout)
        buttons_layout.addWidget(logout_button)

        top_layout.addWidget(buttons_container)
        top_layout.addStretch()
        self.content_layout.addWidget(top_panel)

        # Таблица данных
        self.data_table = QTableView()
        self.data_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setSortingEnabled(False)
        
        header = SortableHeaderView(Qt.Horizontal, self.data_table)
        self.data_table.setHorizontalHeader(header)
        header.sortRequested.connect(self.sort_by_column)
        
        self.data_table.setStyleSheet("""
            QTableView { 
                background-color: white; 
                color: black; 
                font-size: 12px; 
                alternate-background-color: #fafafa; 
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
                cursor: pointer;
            }
            QHeaderView::section:pressed { 
                background-color: #003366;
            }
        """)
        self.content_layout.addWidget(self.data_table, 1)

        # Прокси-модель
        self.proxy_model = CustomFilterProxyModel()
        self.proxy_model.setSourceModel(None)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setDynamicSortFilter(False)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        # Нижняя панель
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

        # ✅ БОКОВОЕ МЕНЮ - правильное позиционирование
        self.side_menu = SideMenu(self)
        self.side_menu.setParent(self)
        self.side_menu.setGeometry(-280, 0, 280, self.height())
        self.side_menu.show()
        
        # ✅ ОВЕРЛЕЙ - поверх контента, но под меню
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.hide()
        self.overlay.mousePressEvent = lambda e: self.toggle_menu()
        
        # ✅ Поднимаем меню на самый верх
        self.side_menu.raise_()

        self.load_table("Пользователи")

    def resizeEvent(self, event):
        """Обработка изменения размера окна."""
        super().resizeEvent(event)
        if hasattr(self, 'side_menu'):
            self.side_menu.setGeometry(-280, 0, 280, self.height())
        if hasattr(self, 'overlay'):
            self.overlay.setGeometry(0, 0, self.width(), self.height())

    def toggle_menu(self):
        """Переключает состояние меню."""
        if self.menu_opened:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        """Открывает меню."""
        self.overlay.show()
        self.overlay.raise_()
        self.side_menu.raise_()
        self.menu_opened = True
        
        # Анимация появления
        self.menu_animation = QPropertyAnimation(self.side_menu, b"pos")
        self.menu_animation.setDuration(300)
        self.menu_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.menu_animation.setStartValue(QPoint(-280, 0))
        self.menu_animation.setEndValue(QPoint(0, 0))
        self.menu_animation.start()

    def close_menu(self):
        """Закрывает меню."""
        self.menu_animation = QPropertyAnimation(self.side_menu, b"pos")
        self.menu_animation.setDuration(300)
        self.menu_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.menu_animation.setStartValue(QPoint(0, 0))
        self.menu_animation.setEndValue(QPoint(-280, 0))
        self.menu_animation.finished.connect(self.on_menu_closed)
        self.menu_animation.start()

    def on_menu_closed(self):
        """Вызывается после закрытия меню."""
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
        
        if is_numeric or is_date:
            self.proxy_model.setSortRole(Qt.DisplayRole)
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

    def open_add_form(self):
        selected_table = TABLES[self.table_selector.currentText()]
        dialog = InputForm(HEADERS[selected_table])
        result = dialog.exec()
        if result == QDialog.Accepted:
            new_data = {field: dialog.input_fields[field].text() for field in dialog.input_fields}
            self.db.insert_record(selected_table, new_data)
            self.reload_current_table()

    def edit_selected_row(self):
        selected_indexes = self.data_table.selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            columns = range(self.data_table.model().columnCount())
            selected_table = TABLES[self.table_selector.currentText()]
            model = self.data_table.model()
            values = {HEADERS[selected_table][col]: model.index(row, col).data() for col in columns}
            
            dialog = InputForm(values)
            result = dialog.exec()
            if result == QDialog.Accepted:
                updated_values = {field: dialog.input_fields[field].text() for field in dialog.input_fields}
                record_id = model.index(row, 0).data()
                self.db.update_record(selected_table, record_id, updated_values)
                self.reload_current_table()
        else:
            QMessageBox.information(self, "Внимание", "Выберите запись для редактирования.")

    def delete_selected_row(self):
        selected_indexes = self.data_table.selectedIndexes()
        if selected_indexes:
            confirm_result = QMessageBox.question(self, "Подтверждение удаления",
                                               "Вы действительно хотите удалить выбранную запись?",
                                               QMessageBox.Yes | QMessageBox.No)
            if confirm_result == QMessageBox.Yes:
                row = selected_indexes[0].row()
                model = self.data_table.model()
                record_id = model.index(row, 0).data()
                self.db.delete_record(TABLES[self.table_selector.currentText()], record_id)
                self.reload_current_table()
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
                for col_idx, value in enumerate(row.values()):
                    text = str(value) if value is not None else ""
                    if len(text) > MAX_CELL_LENGTH:
                        text = text[:MAX_CELL_LENGTH - 1] + "…"

                    item = QStandardItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                    if isinstance(value, (int, float)):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        item.setData(value, Qt.DisplayRole)
                        item.setData(value, Qt.EditRole)
                    elif isinstance(value, (date, datetime)):
                        item.setData(value.isoformat(), Qt.DisplayRole)
                        item.setData(value, Qt.UserRole)
                    else:
                        item.setData(text, Qt.DisplayRole)
                        item.setData(text, Qt.EditRole)

                    model.setItem(row_idx, col_idx, item)

            header = self.data_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            if header.count() > 0:
                header.setSectionResizeMode(header.count() - 1, QHeaderView.ResizeMode.Stretch)

            self.proxy_model.setSourceModel(model)
            self.data_table.setModel(self.proxy_model)
            
            if isinstance(header, SortableHeaderView):
                header.sort_column = -1
                header.sort_ascending = True
            
            self.search_bar.clear()
            self.proxy_model.set_search_text("")
            self.reset_sort()

        except Exception as e:
            print(f"Ошибка при загрузке таблицы '{table_name}': {e}")
            error_model = QStandardItemModel(1, 1)
            error_model.setHorizontalHeaderLabels(["Ошибка"])
            error_model.setItem(0, 0, QStandardItem(str(e)))
            self.proxy_model.setSourceModel(error_model)
            self.data_table.setModel(self.proxy_model)