from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QFormLayout, QGroupBox, QTabWidget,
    QComboBox, QLineEdit, QDateEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from database import Database
from datetime import datetime
from PySide6.QtGui import QColor

class MaterialFlowPage(QMainWindow):
    back_to_table = Signal()
    
    # Цвета
    PRIMARY_COLOR = "#1A529C"
    PRIMARY_DARK = "#0d47a1"
    PRIMARY_LIGHT = "#E3F2FD"
    INCOMING_COLOR = "#27AE60"
    INCOMING_DARK = "#219653"
    OUTGOING_COLOR = "#E74C3C"
    OUTGOING_DARK = "#C0392B"
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.materials_cache = []
        self.suppliers_cache = []
        self.users_cache = []
        self.init_ui()
        self.load_combo_data()
        self.refresh_materials_indicator()
        
    def init_ui(self):
        self.setWindowTitle(f"Приход/расход материалов | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
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
        
        title_label = QLabel("📦 Управление движением материалов")
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
        
        main_layout.addWidget(top_panel)
        
        # ─── Вкладки ─────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.PRIMARY_COLOR};
                background-color: #FAFAFA;
            }}
            QTabBar::tab {{
                background-color: {self.PRIMARY_LIGHT};
                color: {self.PRIMARY_COLOR};
                padding: 12px 30px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #D6EAF8;
            }}
        """)
        
        # Вкладка Приход
        self.incoming_tab = QWidget()
        self.incoming_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_incoming_tab()
        self.tabs.addTab(self.incoming_tab, "📥 Приход материалов")
        
        # Вкладка Расход
        self.outgoing_tab = QWidget()
        self.outgoing_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_outgoing_tab()
        self.tabs.addTab(self.outgoing_tab, "📤 Расход материалов")
        
        # Устанавливаем первую вкладку активной
        self.tabs.setCurrentIndex(0)
        
        main_layout.addWidget(self.tabs, 1)
        
    def setup_incoming_tab(self):
        """Настройка вкладки Приход"""
        layout = QVBoxLayout(self.incoming_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # ─── Индикация запасов ─────────────────────────────────
        self.incoming_indicator_label = QLabel("📊 Текущие запасы материалов:")
        self.incoming_indicator_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.incoming_indicator_label.setStyleSheet("color: #2C3E50;")
        layout.addWidget(self.incoming_indicator_label)
        
        self.incoming_indicator_table = QTableWidget()
        self.incoming_indicator_table.setColumnCount(5)
        self.incoming_indicator_table.setHorizontalHeaderLabels([
            "Материал", "Категория", "Текущий остаток", "Мин. запас", "Статус"
        ])
        self.incoming_indicator_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.incoming_indicator_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.incoming_indicator_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.incoming_indicator_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(self.incoming_indicator_table)
        
        # ─── Форма прихода ─────────────────────────────────────
        form_group = self._create_group_box("➕ Добавить приход материала", self.INCOMING_COLOR)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        
        # Материал
        self.incoming_material = QComboBox()
        self.incoming_material.setMinimumHeight(40)
        self.incoming_material.setStyleSheet(self._input_style())
        self.incoming_material.currentIndexChanged.connect(self.on_incoming_material_changed)
        form_layout.addRow("  Материал:", self.incoming_material)
        
        # Количество
        self.incoming_quantity = QLineEdit()
        self.incoming_quantity.setPlaceholderText("Например: 100")
        self.incoming_quantity.setMinimumHeight(40)
        self.incoming_quantity.setStyleSheet(self._input_style())
        form_layout.addRow("  Количество:", self.incoming_quantity)
        
        # Поставщик
        self.incoming_supplier = QComboBox()
        self.incoming_supplier.setEditable(True)
        self.incoming_supplier.setMinimumHeight(40)
        self.incoming_supplier.setStyleSheet(self._input_style())
        form_layout.addRow("  Поставщик:", self.incoming_supplier)
        
        # Номер документа
        self.incoming_doc_number = QLineEdit()
        self.incoming_doc_number.setPlaceholderText("ПРИХ-001/2025")
        self.incoming_doc_number.setMinimumHeight(40)
        self.incoming_doc_number.setStyleSheet(self._input_style())
        form_layout.addRow("  Номер документа:", self.incoming_doc_number)
        
        # Дата
        self.incoming_doc_date = QDateEdit()
        self.incoming_doc_date.setCalendarPopup(True)
        self.incoming_doc_date.setDate(QDate.currentDate())
        self.incoming_doc_date.setMinimumHeight(40)
        self.incoming_doc_date.setStyleSheet(self._input_style())
        form_layout.addRow("  Дата документа:", self.incoming_doc_date)
        
        # Примечание
        self.incoming_notes = QTextEdit()
        self.incoming_notes.setPlaceholderText("Дополнительная информация...")
        self.incoming_notes.setMaximumHeight(80)
        self.incoming_notes.setStyleSheet(self._input_style())
        form_layout.addRow("  Примечание:", self.incoming_notes)
        
        # Кнопка добавить
        add_button = QPushButton("✅ Провести приход")
        add_button.setFixedHeight(45)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.INCOMING_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.INCOMING_DARK};
            }}
        """)
        add_button.clicked.connect(self.add_incoming)
        form_layout.addRow(add_button)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
    def setup_outgoing_tab(self):
        """Настройка вкладки Расход"""
        layout = QVBoxLayout(self.outgoing_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # ─── Индикация запасов ─────────────────────────────────
        self.outgoing_indicator_label = QLabel("📊 Текущие запасы материалов:")
        self.outgoing_indicator_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.outgoing_indicator_label.setStyleSheet("color: #2C3E50;")
        layout.addWidget(self.outgoing_indicator_label)
        
        self.outgoing_indicator_table = QTableWidget()
        self.outgoing_indicator_table.setColumnCount(5)
        self.outgoing_indicator_table.setHorizontalHeaderLabels([
            "Материал", "Категория", "Текущий остаток", "Мин. запас", "Статус"
        ])
        self.outgoing_indicator_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.outgoing_indicator_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.outgoing_indicator_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.outgoing_indicator_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #E74C3C;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(self.outgoing_indicator_table)
        
        # ─── Форма расхода ─────────────────────────────────────
        form_group = self._create_group_box("➖ Списать материал", self.OUTGOING_COLOR)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        
        # Материал
        self.outgoing_material = QComboBox()
        self.outgoing_material.setMinimumHeight(40)
        self.outgoing_material.setStyleSheet(self._input_style())
        self.outgoing_material.currentIndexChanged.connect(self.on_outgoing_material_changed)
        form_layout.addRow("  Материал:", self.outgoing_material)
        
        # Доступно (информация)
        self.outgoing_available = QLabel("Доступно: 0 шт")
        self.outgoing_available.setStyleSheet("font-weight: bold; color: #7F8C8D; padding: 8px;")
        form_layout.addRow("  Доступно:", self.outgoing_available)
        
        # Количество
        self.outgoing_quantity = QLineEdit()
        self.outgoing_quantity.setPlaceholderText("Например: 50")
        self.outgoing_quantity.setMinimumHeight(40)
        self.outgoing_quantity.setStyleSheet(self._input_style())
        form_layout.addRow("  Количество:", self.outgoing_quantity)
        
        # Номер документа
        self.outgoing_doc_number = QLineEdit()
        self.outgoing_doc_number.setPlaceholderText("РАСХ-015/2025")
        self.outgoing_doc_number.setMinimumHeight(40)
        self.outgoing_doc_number.setStyleSheet(self._input_style())
        form_layout.addRow("  Номер документа:", self.outgoing_doc_number)
        
        # Дата
        self.outgoing_doc_date = QDateEdit()
        self.outgoing_doc_date.setCalendarPopup(True)
        self.outgoing_doc_date.setDate(QDate.currentDate())
        self.outgoing_doc_date.setMinimumHeight(40)
        self.outgoing_doc_date.setStyleSheet(self._input_style())
        form_layout.addRow("  Дата документа:", self.outgoing_doc_date)
        
        # Примечание
        self.outgoing_notes = QTextEdit()
        self.outgoing_notes.setPlaceholderText("Например: Отгрузка на объект...")
        self.outgoing_notes.setMaximumHeight(80)
        self.outgoing_notes.setStyleSheet(self._input_style())
        form_layout.addRow("  Примечание:", self.outgoing_notes)
        
        # Кнопка добавить
        add_button = QPushButton("❌ Провести расход")
        add_button.setFixedHeight(45)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.OUTGOING_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.OUTGOING_DARK};
            }}
        """)
        add_button.clicked.connect(self.add_outgoing)
        form_layout.addRow(add_button)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
    def _create_group_box(self, title: str, color: str) -> QGroupBox:
        """Создаёт группу с единым стилем"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                color: {color};
                border: 2px solid {color};
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
            QComboBox, QLineEdit, QTextEdit, QDateEdit {{
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 13px;
                color: #222222;
            }}
            QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {{
                border: 2px solid {self.PRIMARY_COLOR};
                background-color: #FFFFFF;
                outline: none;
            }}
        """
        
    def load_combo_data(self):
        """Загружает данные для ComboBox с использованием JOIN"""
        try:
            # Загрузка материалов с категориями (JOIN)
            materials_query = """
                SELECT m.id, m.name, m.quantity, m.unit, m.min_quantity, c.name as category_name
                FROM materials m
                LEFT JOIN categories c ON m.category_id = c.id
                ORDER BY m.name
            """
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(materials_query)
            self.materials_cache = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Заполняем ComboBox материалов
            self.incoming_material.clear()
            self.outgoing_material.clear()
            for mat in self.materials_cache:
                mat_id, name, qty, unit, min_qty, category = mat
                display_text = f"{name} ({category or 'Без категории'}) - {qty} {unit}"
                self.incoming_material.addItem(display_text, mat_id)
                self.outgoing_material.addItem(display_text, mat_id)
            
            # Загрузка поставщиков (из materials.supplier - уникальные)
            suppliers_query = """
                SELECT DISTINCT supplier 
                FROM materials 
                WHERE supplier IS NOT NULL AND supplier != ''
                ORDER BY supplier
            """
            cursor = conn.cursor() if (conn := self.db.get_connection()) else None
            if cursor:
                cursor.execute(suppliers_query)
                self.suppliers_cache = [row[0] for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                
                self.incoming_supplier.addItems(self.suppliers_cache)
            
            # Загрузка пользователей
            users_query = "SELECT id, full_name FROM users WHERE is_active = TRUE ORDER BY full_name"
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(users_query)
            self.users_cache = cursor.fetchall()
            cursor.close()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def refresh_materials_indicator(self):
        """Обновляет таблицу индикации запасов"""
        try:
            query = """
                SELECT m.id, m.name, m.quantity, m.min_quantity, m.unit, c.name as category_name
                FROM materials m
                LEFT JOIN categories c ON m.category_id = c.id
                ORDER BY m.name
            """
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            materials = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Обновляем обе таблицы
            for table in [self.incoming_indicator_table, self.outgoing_indicator_table]:
                table.setRowCount(len(materials))
                for row_idx, mat in enumerate(materials):
                    mat_id, name, qty, min_qty, unit, category = mat
                    
                    # Определяем статус и цвет
                    if qty == 0:
                        status = "⚫ Нет в наличии"
                        color = "#2C3E50"
                        bg_color = "#F5F5F5"
                    elif qty <= min_qty:
                        percentage = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🔴 Критически мало ({percentage:.0f}%)"
                        color = "#E74C3C"
                        bg_color = "#FADBD8"
                    elif qty <= min_qty * 1.5:
                        percentage = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🟡 Заканчивается ({percentage:.0f}%)"
                        color = "#F39C12"
                        bg_color = "#FDEBD0"
                    else:
                        percentage = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🟢 В достатке ({percentage:.0f}%)"
                        color = "#27AE60"
                        bg_color = "#D5F5E3"
                    
                    # Заполняем ячейки
                    table.setItem(row_idx, 0, QTableWidgetItem(name))
                    table.setItem(row_idx, 1, QTableWidgetItem(category or "Без категории"))
                    table.setItem(row_idx, 2, QTableWidgetItem(f"{qty} {unit}"))
                    table.setItem(row_idx, 3, QTableWidgetItem(f"{min_qty} {unit}"))
                    
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(Qt.white if qty <= min_qty else Qt.black)
                    status_item.setBackground(Qt.white if qty == 0 else Qt.transparent)
                    table.setItem(row_idx, 4, status_item)
                    
                    # Устанавливаем цвет фона для всей строки
                    for col in range(5):
                        item = table.item(row_idx, col)
                        if item:
                            item.setBackground(Qt.white if qty == 0 else 
                                             QColor(bg_color) if qty <= min_qty * 1.5 else Qt.white)
                            
        except Exception as e:
            print(f"Ошибка при обновлении индикации: {e}")
            
    def on_incoming_material_changed(self, index):
        """Обработка изменения материала на вкладке Приход"""
        if index >= 0 and index < len(self.materials_cache):
            mat = self.materials_cache[index]
            # Можно добавить дополнительную логику
            
    def on_outgoing_material_changed(self, index):
        """Обработка изменения материала на вкладке Расход"""
        if index >= 0 and index < len(self.materials_cache):
            mat = self.materials_cache[index]
            mat_id, name, qty, unit, min_qty, category = mat
            self.outgoing_available.setText(f"Доступно: {qty} {unit}")
            
    def add_incoming(self):
        """Добавление прихода материала"""
        try:
            # Получаем данные из формы
            material_idx = self.incoming_material.currentIndex()
            if material_idx < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите материал!")
                return
                
            material_id = self.incoming_material.itemData(material_idx)
            quantity = self.incoming_quantity.text().strip()
            supplier = self.incoming_supplier.currentText().strip()
            doc_number = self.incoming_doc_number.text().strip()
            doc_date = self.incoming_doc_date.date().toPython()
            notes = self.incoming_notes.toPlainText().strip()
            
            # Валидация
            if not quantity:
                QMessageBox.warning(self, "Ошибка", "Введите количество!")
                return
                
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть положительным числом!")
                return
                
            if not doc_number:
                QMessageBox.warning(self, "Ошибка", "Введите номер документа!")
                return
            
            # Получаем текущее количество материала
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM materials WHERE id = %s", (material_id,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                cursor.close()
                conn.close()
                return
                
            current_qty = result[0]
            new_qty = current_qty + quantity
            
            # Начинаем транзакцию
            try:
                # Обновляем количество материала
                cursor.execute(
                    "UPDATE materials SET quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_qty, material_id)
                )
                
                # Добавляем транзакцию
                cursor.execute("""
                    INSERT INTO transactions 
                    (material_id, user_id, quantity, transaction_type, document_number, document_date, notes)
                    VALUES (%s, %s, %s, 'incoming', %s, %s, %s)
                """, (material_id, self.user_data['id'], quantity, doc_number, doc_date, notes))
                
                conn.commit()
                
                QMessageBox.information(
                    self, "Успешно",
                    f"Приход проведён!\n"
                    f"Материал: {self.incoming_material.currentText()}\n"
                    f"Количество: +{quantity}\n"
                    f"Новый остаток: {new_qty}"
                )
                
                # Очищаем форму и обновляем данные
                self.incoming_quantity.clear()
                self.incoming_doc_number.clear()
                self.incoming_notes.clear()
                self.load_combo_data()
                self.refresh_materials_indicator()
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось провести приход: {str(e)}")
            
    def add_outgoing(self):
        """Добавление расхода материала"""
        try:
            # Получаем данные из формы
            material_idx = self.outgoing_material.currentIndex()
            if material_idx < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите материал!")
                return
                
            material_id = self.outgoing_material.itemData(material_idx)
            quantity = self.outgoing_quantity.text().strip()
            doc_number = self.outgoing_doc_number.text().strip()
            doc_date = self.outgoing_doc_date.date().toPython()
            notes = self.outgoing_notes.toPlainText().strip()
            
            # Валидация
            if not quantity:
                QMessageBox.warning(self, "Ошибка", "Введите количество!")
                return
                
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть положительным числом!")
                return
                
            if not doc_number:
                QMessageBox.warning(self, "Ошибка", "Введите номер документа!")
                return
            
            # Получаем текущее количество материала
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM materials WHERE id = %s", (material_id,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                cursor.close()
                conn.close()
                return
                
            current_qty = result[0]
            
            # Проверка: нельзя списать больше, чем есть (максимум до 0)
            if quantity > current_qty:
                QMessageBox.warning(
                    self, "Недостаточно материала",
                    f"На складе доступно: {current_qty} шт\n"
                    f"Вы пытаетесь списать: {quantity} шт\n\n"
                    f"Нельзя уйти в минус!"
                )
                cursor.close()
                conn.close()
                return
                
            new_qty = current_qty - quantity
            
            # Начинаем транзакцию
            try:
                # Обновляем количество материала
                cursor.execute(
                    "UPDATE materials SET quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_qty, material_id)
                )
                
                # Добавляем транзакцию
                cursor.execute("""
                    INSERT INTO transactions 
                    (material_id, user_id, quantity, transaction_type, document_number, document_date, notes)
                    VALUES (%s, %s, %s, 'outgoing', %s, %s, %s)
                """, (material_id, self.user_data['id'], quantity, doc_number, doc_date, notes))
                
                conn.commit()
                
                QMessageBox.information(
                    self, "Успешно",
                    f"Расход проведён!\n"
                    f"Материал: {self.outgoing_material.currentText()}\n"
                    f"Количество: -{quantity}\n"
                    f"Новый остаток: {new_qty}"
                )
                
                # Очищаем форму и обновляем данные
                self.outgoing_quantity.clear()
                self.outgoing_doc_number.clear()
                self.outgoing_notes.clear()
                self.load_combo_data()
                self.refresh_materials_indicator()
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось провести расход: {str(e)}")
            
    def go_back(self):
        """Возврат к таблицам"""
        self.back_to_table.emit()
        self.close()
        
    def logout(self):
        """Выход из аккаунта"""
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()

