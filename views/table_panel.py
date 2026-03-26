import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem
from datetime import date
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
    "users": [0],  # ID
    "categories": [0],  # ID
    "suppliers": [0],  # ID
    "materials": [0, 2, 4, 5],  # ID, Количество, Цена, Мин. запас
    "transactions": [0, 3],  # ID, Количество
    "material_history": [0, 2, 3, 4]  # ID, Было, Стало, Разница
}

MAX_CELL_LENGTH = 60


class InputForm(QDialog):
    """Форма для ввода данных."""
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
        """Проверяет введённые данные и сохраняет изменения."""
        valid = all(self.input_fields[field].text() != '' for field in self.input_fields)
        if valid:
            data = {field: self.input_fields[field].text() for field in self.input_fields}
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Необходимо заполнить все поля.")


class SortableHeaderView(QHeaderView):
    """Заголовок таблицы с индикаторами сортировки."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.sort_indicator_section = -1
        self.sort_order = Qt.AscendingOrder
        self.setSectionsClickable(True)
        self.sectionClicked.connect(self.on_section_clicked)
    
    def on_section_clicked(self, logical_index):
        """Обработка клика по заголовку столбца."""
        if self.sort_indicator_section == logical_index:
            # Переключаем порядок сортировки
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_indicator_section = logical_index
            self.sort_order = Qt.AscendingOrder
        
        self.viewport().update()
        # Сигнал для сортировки в таблице
        self.parent().sort_by_column(logical_index, self.sort_order)
    
    def paintSection(self, painter, rect, logical_index):
        """Рисует заголовок столбца с индикатором сортировки."""
        super().paintSection(painter, rect, logical_index)
        
        if self.sort_indicator_section == logical_index:
            painter.save()
            
            # Размер стрелки
            arrow_size = 8
            padding = 10
            
            # Координаты для стрелки
            if self.sort_order == Qt.AscendingOrder:
                # Стрелка вверх ▲
                points = [
                    (rect.right() - padding, rect.center().y() - arrow_size),
                    (rect.right() - padding + arrow_size, rect.center().y()),
                    (rect.right() - padding - arrow_size, rect.center().y())
                ]
            else:
                # Стрелка вниз ▼
                points = [
                    (rect.right() - padding, rect.center().y() + arrow_size),
                    (rect.right() - padding + arrow_size, rect.center().y()),
                    (rect.right() - padding - arrow_size, rect.center().y())
                ]
            
            from PySide6.QtGui import QPolygon, QPen, QBrush
            from PySide6.QtCore import QPoint
            
            polygon = QPolygon([QPoint(x, y) for x, y in points])
            painter.setPen(QPen(Qt.white, 2))
            painter.setBrush(QBrush(Qt.white))
            painter.drawPolygon(polygon)
            
            painter.restore()


class TablePanel(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.current_table_name = None
        self.search_text = ""
        self.init_ui()

    def init_ui(self):
        """Инициализация графического интерфейса."""
        self.setWindowTitle(f"Управление складом | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(1024, 768)

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Верхняя панель
        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet("background-color: #F0F8FF; border-bottom: 2px solid #1A529C;")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(20, 0, 20, 0)

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
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
        """)
        add_button.clicked.connect(self.open_add_form)
        buttons_layout.addWidget(add_button)

        edit_button = QPushButton("Редактировать")
        edit_button.setFixedSize(100, 32)
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        edit_button.clicked.connect(self.edit_selected_row)
        buttons_layout.addWidget(edit_button)

        delete_button = QPushButton("Удалить")
        delete_button.setFixedSize(100, 32)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        delete_button.clicked.connect(self.delete_selected_row)
        buttons_layout.addWidget(delete_button)

        # ✅ ПОИСК - полное совпадение по ячейкам
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Поиск (полное совпадение)...")
        search_bar.textChanged.connect(self.apply_search_filter)
        search_bar.setFixedWidth(200)
        buttons_layout.addWidget(search_bar)

        # ✅ КНОПКА "ФИЛЬТР" УДАЛЕНА

        top_layout.addWidget(buttons_container)
        top_layout.addStretch()
        main_layout.addWidget(top_panel)

        # Таблица данных
        self.data_table = QTableView()
        self.data_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setSortingEnabled(False)  # Отключаем стандартную сортировку
        
        # ✅ КАСТОМНЫЙ ЗАГОЛОВОК С ИНДИКАТОРАМИ
        header = SortableHeaderView(Qt.Horizontal, self.data_table)
        self.data_table.setHorizontalHeader(header)
        
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
            }
            QTableView::item {
                padding-left: 5px;
                padding-right: 5px;
            }
        """)
        main_layout.addWidget(self.data_table)

        # Прокси-модель для фильтрации
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(None)
        self.proxy_model.setDynamicSortFilter(False)  # Отключаем динамическую фильтрацию
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Нижняя панель
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(40)
        bottom_panel.setStyleSheet("background-color: #F5F5F5; border-top: 1px solid #E0E0E0;")
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        version_label = QLabel("Склад материалов v1.0 | PUTEVI")
        bottom_layout.addWidget(version_label)
        bottom_layout.addStretch()
        main_layout.addWidget(bottom_panel)

        self.load_table("Пользователи")

    def open_add_form(self):
        """Открывает форму добавления записи."""
        selected_table = TABLES[self.table_selector.currentText()]
        dialog = InputForm(HEADERS[selected_table])
        result = dialog.exec()
        if result == QDialog.Accepted:
            new_data = {field: dialog.input_fields[field].text() for field in dialog.input_fields}
            self.db.insert_record(selected_table, new_data)
            self.reload_current_table()

    def edit_selected_row(self):
        """Редактирует выбранную строку."""
        selected_indexes = self.data_table.selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            columns = range(self.data_table.model().columnCount())
            selected_table = TABLES[self.table_selector.currentText()]
            values = {HEADERS[selected_table][col]: self.data_table.model().index(row, col).data() for col in columns}
            dialog = InputForm(values)
            result = dialog.exec()
            if result == QDialog.Accepted:
                updated_values = {field: dialog.input_fields[field].text() for field in dialog.input_fields}
                self.db.update_record(selected_table, values['ID'], updated_values)
                self.reload_current_table()
        else:
            QMessageBox.information(self, "Внимание", "Выберите запись для редактирования.")

    def delete_selected_row(self):
        """Удаляет выбранную строку."""
        selected_indexes = self.data_table.selectedIndexes()
        if selected_indexes:
            confirm_result = QMessageBox.question(self, "Подтверждение удаления",
                                               "Вы действительно хотите удалить выбранную запись?",
                                               QMessageBox.Yes | QMessageBox.No)
            if confirm_result == QMessageBox.Yes:
                row = selected_indexes[0].row()
                record_id = self.data_table.model().index(row, 0).data()
                self.db.delete_record(TABLES[self.table_selector.currentText()], record_id)
                self.reload_current_table()
        else:
            QMessageBox.information(self, "Внимание", "Выберите запись для удаления.")

    def apply_search_filter(self, text):
        """
        ✅ ПОИСК - полное совпадение по любой ячейке в строке.
        Если текст найден в любой ячейке строки - строка отображается.
        """
        self.search_text = text.strip().lower()
        self.proxy_model.invalidateFilter()

    def sort_by_column(self, logical_index, sort_order):
        """
        ✅ СОРТИРОВКА по столбцу с учётом типа данных.
        """
        table_name = TABLES[self.table_selector.currentText()]
        
        # Проверяем, является ли столбец числовым
        is_numeric = logical_index in NUMERIC_COLUMNS.get(table_name, [])
        
        if is_numeric:
            # Для числовых столбцов устанавливаем режим сортировки
            self.proxy_model.setSortKey(logical_index)
            self.proxy_model.setSortOrder(sort_order)
            # Включаем численную сортировку
            self.proxy_model.setSortRole(Qt.DisplayRole)
        else:
            # Для текстовых столбцов - строковая сортировка
            self.proxy_model.setSortKey(logical_index)
            self.proxy_model.setSortOrder(sort_order)
        
        self.proxy_model.sort(logical_index, sort_order)

    def reload_current_table(self):
        """Перезагружает текущую таблицу."""
        self.load_table(self.table_selector.currentText())

    def load_table(self, display_name: str):
        """Загружает данные из указанной таблицы в интерфейс."""
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

                    # ✅ Числовые значения - выравнивание по центру и роль для сортировки
                    if isinstance(value, (int, float)):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        item.setData(value, Qt.DisplayRole)  # Для правильной численной сортировки
                    else:
                        item.setData(text.lower(), Qt.DisplayRole)  # Для регистронезависимой сортировки

                    model.setItem(row_idx, col_idx, item)

            # Настройка заголовков
            header = self.data_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            if header.count() > 0:
                header.setSectionResizeMode(header.count() - 1, QHeaderView.ResizeMode.Stretch)

            # ✅ НАСТРОЙКА ПРОКСИ-МОДЕЛИ
            self.proxy_model.setSourceModel(model)
            self.proxy_model.setFilterKeyColumn(-1)  # Поиск по всем столбцам
            self.data_table.setModel(self.proxy_model)
            
            # Сброс индикатора сортировки при смене таблицы
            if isinstance(header, SortableHeaderView):
                header.sort_indicator_section = -1

        except Exception as e:
            print(f"Ошибка при загрузке таблицы '{table_name}': {e}")
            error_model = QStandardItemModel(1, 1)
            error_model.setHorizontalHeaderLabels(["Ошибка"])
            error_model.setItem(0, 0, QStandardItem(str(e)))
            self.proxy_model.setSourceModel(error_model)
            self.data_table.setModel(self.proxy_model)


# Переопределяем метод filterAcceptsRow для полного совпадения
class CustomFilterProxyModel(QSortFilterProxyModel):
    """Прокси-модель с поиском по полному совпадению в любой ячейке."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
    
    def set_search_text(self, text):
        self.search_text = text.strip().lower()
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row, source_parent):
        """
        ✅ Если поиск пустой - показываем все строки.
        ✅ Если поиск есть - показываем строки где текст полностью совпадает с любой ячейкой.
        """
        if not self.search_text:
            return True
        
        source_model = self.sourceModel()
        if source_model is None:
            return True
        
        # Проверяем все ячейки в строке
        for column in range(source_model.columnCount()):
            index = source_model.index(source_row, column, source_parent)
            cell_value = str(source_model.data(index, Qt.DisplayRole) or "").lower()
            
            # ✅ ПОЛНОЕ СОВПАДЕНИЕ (можно изменить на 'in' для частичного)
            if cell_value == self.search_text:
                return True
        
        return False