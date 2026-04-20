from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QGroupBox, QFileDialog, QMessageBox, QProgressBar,
    QRadioButton, QButtonGroup, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
from utils.export_import_helper import ExportImportHelper


class ExportImportDialog(QDialog):
    """Диалог экспорта/импорта данных"""
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Экспорт/Импорт данных")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("Экспорт и импорт данных")
        title.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A529C;")
        layout.addWidget(title)
        
        # Выбор режима
        mode_group = QGroupBox("Режим работы")
        mode_layout = QHBoxLayout(mode_group)
        
        self.export_radio = QRadioButton("Экспорт данных")
        self.import_radio = QRadioButton("Импорт данных")
        self.export_radio.setChecked(True)
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.export_radio)
        self.mode_group.addButton(self.import_radio)
        
        mode_layout.addWidget(self.export_radio)
        mode_layout.addWidget(self.import_radio)
        mode_layout.addStretch()
        
        layout.addWidget(mode_group)
        
        # Контейнер для контента
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Экспорт
        self.setup_export_ui()
        
        # Импорт
        self.setup_import_ui()
        self.import_widget.setVisible(False)
        
        layout.addWidget(self.content_widget)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.execute_button = QPushButton("Экспортировать")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #1A529C;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #164786;
            }
            QPushButton:pressed {
                background-color: #123A6E;
            }
        """)
        self.execute_button.clicked.connect(self.execute_operation)
        button_layout.addWidget(self.execute_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.setMinimumHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Переключение режима
        self.export_radio.toggled.connect(self.on_mode_changed)
    
    def setup_export_ui(self):
        """Настройка UI для экспорта"""
        self.export_widget = QWidget()
        export_layout = QVBoxLayout(self.export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.setSpacing(10)
        
        # Выбор таблиц
        tables_group = QGroupBox("Выберите таблицы для экспорта")
        tables_layout = QVBoxLayout(tables_group)
        
        # Кнопка "Выбрать все"
        select_all_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Выбрать все таблицы")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        select_all_layout.addWidget(self.select_all_checkbox)
        select_all_layout.addStretch()
        tables_layout.addLayout(select_all_layout)
        
        # Чекбоксы таблиц
        self.table_checkboxes = {}
        from views.table_panel import TABLES
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(250)
        
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(5, 5, 5, 5)
        
        for display_name in TABLES.keys():
            cb = QCheckBox(display_name)
            cb.setChecked(True)
            self.table_checkboxes[display_name] = cb
            checkbox_layout.addWidget(cb)
        
        checkbox_layout.addStretch()
        scroll_area.setWidget(checkbox_container)
        tables_layout.addWidget(scroll_area)
        
        export_layout.addWidget(tables_group)
        
        # Выбор формата
        format_group = QGroupBox("Формат экспорта")
        format_layout = QVBoxLayout(format_group)
        
        self.xlsx_radio = QRadioButton("Excel (.xlsx)")
        self.pdf_radio = QRadioButton("PDF (.pdf)")
        self.xlsx_radio.setChecked(True)
        
        format_layout.addWidget(self.xlsx_radio)
        format_layout.addWidget(self.pdf_radio)
        
        export_layout.addWidget(format_group)
        
        # Путь к файлу
        file_group = QGroupBox("Файл экспорта")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("Не выбрано")
        self.file_path_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self.file_path_label, 1)
        
        browse_button = QPushButton("Обзор...")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #17A2B8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        browse_button.clicked.connect(self.browse_export_file)
        file_layout.addWidget(browse_button)
        
        export_layout.addWidget(file_group)
        export_layout.addStretch()
        
        self.content_layout.addWidget(self.export_widget)
    
    def setup_import_ui(self):
        """Настройка UI для импорта"""
        self.import_widget = QWidget()
        import_layout = QVBoxLayout(self.import_widget)
        import_layout.setContentsMargins(0, 0, 0, 0)
        import_layout.setSpacing(10)
        
        # Выбор файла
        file_group = QGroupBox("Файл для импорта")
        file_layout = QHBoxLayout(file_group)
        
        self.import_file_label = QLabel("Не выбрано")
        self.import_file_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self.import_file_label, 1)
        
        browse_button = QPushButton("Обзор...")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #17A2B8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        browse_button.clicked.connect(self.browse_import_file)
        file_layout.addWidget(browse_button)
        
        import_layout.addWidget(file_group)
        
        # Выбор таблицы
        table_group = QGroupBox("Таблица для импорта")
        table_layout = QVBoxLayout(table_group)
        
        from views.table_panel import TABLES
        self.import_table_combo = QCheckBoxGroup(table_group)
        
        for display_name in TABLES.keys():
            cb = QCheckBox(display_name)
            self.import_table_combo.addButton(cb)
            table_layout.addWidget(cb)
        
        import_layout.addWidget(table_group)
        
        # Настройки импорта
        options_group = QGroupBox("Настройки импорта")
        options_layout = QVBoxLayout(options_group)
        
        self.skip_duplicates_checkbox = QCheckBox("Пропускать дубликаты (по уникальным полям)")
        self.skip_duplicates_checkbox.setChecked(True)
        options_layout.addWidget(self.skip_duplicates_checkbox)
        
        import_layout.addWidget(options_group)
        import_layout.addStretch()
        
        self.content_layout.addWidget(self.import_widget)
    
    def on_mode_changed(self):
        """Переключение между экспортом и импортом"""
        if self.export_radio.isChecked():
            self.export_widget.setVisible(True)
            self.import_widget.setVisible(False)
            self.execute_button.setText("Экспортировать")
        else:
            self.export_widget.setVisible(False)
            self.import_widget.setVisible(True)
            self.execute_button.setText("Импортировать")
    
    def on_select_all_changed(self, state):
        """Выбор/снятие всех таблиц"""
        for cb in self.table_checkboxes.values():
            cb.setChecked(state == Qt.Checked)
    
    def browse_export_file(self):
        """Выбор файла для экспорта"""
        if self.xlsx_radio.isChecked():
            file_filter = "Excel файлы (*.xlsx)"
            default_ext = ".xlsx"
        else:
            file_filter = "PDF файлы (*.pdf)"
            default_ext = ".pdf"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            f"export{default_ext}",
            file_filter
        )
        
        if filepath:
            self.file_path_label.setText(filepath)
    
    def browse_import_file(self):
        """Выбор файла для импорта"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для импорта",
            "",
            "Excel файлы (*.xlsx)"
        )
        
        if filepath:
            self.import_file_label.setText(filepath)
    
    def execute_operation(self):
        """Выполнение операции экспорта/импорта"""
        if self.export_radio.isChecked():
            self.do_export()
        else:
            self.do_import()
    
    def do_export(self):
        """Экспорт данных"""
        # Проверяем выбор таблиц
        selected_tables = {
            name: table_name 
            for name, table_name in self.get_tables_mapping().items()
            if self.table_checkboxes[name].isChecked()
        }
        
        if not selected_tables:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну таблицу")
            return
        
        # Проверяем путь
        filepath = self.file_path_label.text()
        if not filepath or filepath == "Не выбрано":
            QMessageBox.warning(self, "Ошибка", "Выберите файл для сохранения")
            return
        
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.execute_button.setEnabled(False)
        
        # Определяем формат
        if self.xlsx_radio.isChecked():
            success = ExportImportHelper.export_to_xlsx(
                self.db, 
                selected_tables, 
                filepath
            )
        else:
            success = ExportImportHelper.export_to_pdf(
                self.db,
                selected_tables,
                filepath
            )
        
        self.progress_bar.setVisible(False)
        self.execute_button.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, 
                "Успешно", 
                f"Данные успешно экспортированы в:\n{filepath}"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось экспортировать данные")
    
    def do_import(self):
        """Импорт данных"""
        # Проверяем файл
        filepath = self.import_file_label.text()
        if not filepath or filepath == "Не выбрано":
            QMessageBox.warning(self, "Ошибка", "Выберите файл для импорта")
            return
        
        # Проверяем выбор таблицы
        selected_table = None
        from views.table_panel import TABLES
        
        for display_name, table_name in TABLES.items():
            # Ищем выбранный чекбокс (упрощенно - первый выбранный)
            if hasattr(self, 'import_table_combo'):
                # Здесь нужна логика получения выбранной таблицы
                pass
        
        # Для простоты - берем первую выбранную
        # В реальной реализации нужно доработать UI
        QMessageBox.information(
            self, 
            "Информация", 
            "Импорт данных будет реализован в следующей версии"
        )
    
    def get_tables_mapping(self):
        """Возвращает маппинг таблиц"""
        from views.table_panel import TABLES
        return TABLES


class QCheckBoxGroup(QWidget):
    """Простая группа чекбоксов"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
    
    def addButton(self, button):
        self.buttons.append(button)
        self.layout.addWidget(button)
    
    def checkedButtons(self):
        return [btn for btn in self.buttons if btn.isChecked()]