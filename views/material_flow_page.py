from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QFormLayout, QGroupBox, QTabWidget,
    QComboBox, QLineEdit, QDateEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor
from database import Database
from datetime import datetime

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
        self.init_ui()
        self.load_combo_data()
        self.refresh_all_data()
        
    def init_ui(self):
        self.setWindowTitle(f"Приход/расход материалов | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 750)
        
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
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #D6EAF8;
            }}
        """)
        
        # 1. Приход
        self.incoming_tab = QWidget()
        self.incoming_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_incoming_tab()
        self.tabs.addTab(self.incoming_tab, "📥 Приход")
        
        # 2. Расход
        self.outgoing_tab = QWidget()
        self.outgoing_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_outgoing_tab()
        self.tabs.addTab(self.outgoing_tab, "📤 Расход")
        
        # 3. Информация по материалам
        self.materials_info_tab = QWidget()
        self.materials_info_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_materials_info_tab()
        self.tabs.addTab(self.materials_info_tab, "📦 Материалы")
        
        # 4. История движений
        self.history_tab = QWidget()
        self.history_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_history_tab()
        self.tabs.addTab(self.history_tab, "📜 История")
        
        self.tabs.setCurrentIndex(0)
        main_layout.addWidget(self.tabs, 1)
        
    def setup_incoming_tab(self):
        layout = QVBoxLayout(self.incoming_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Индикация запасов
        self.incoming_indicator_label = QLabel("📊 Текущие запасы материалов:")
        self.incoming_indicator_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.incoming_indicator_label.setStyleSheet("color: #2C3E50;")
        layout.addWidget(self.incoming_indicator_label)
        
        self.incoming_indicator_table = QTableWidget()
        self.incoming_indicator_table.setColumnCount(5)
        self.incoming_indicator_table.setHorizontalHeaderLabels([
            "Материал", "Категория", "Остаток", "Мин. запас", "Статус"
        ])
        self.incoming_indicator_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.incoming_indicator_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.incoming_indicator_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.incoming_indicator_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
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
        
        # Форма прихода
        form_group = self._create_group_box("➕ Добавить приход", self.INCOMING_COLOR)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        
        self.incoming_material = QComboBox()
        self.incoming_material.setMinimumHeight(40)
        self.incoming_material.setStyleSheet(self._input_style())
        form_layout.addRow("Материал:", self.incoming_material)
        
        self.incoming_quantity = QLineEdit()
        self.incoming_quantity.setPlaceholderText("Количество")
        self.incoming_quantity.setMinimumHeight(40)
        self.incoming_quantity.setStyleSheet(self._input_style())
        form_layout.addRow("Количество:", self.incoming_quantity)
        
        self.incoming_supplier = QComboBox()
        self.incoming_supplier.setEditable(True)
        self.incoming_supplier.setMinimumHeight(40)
        self.incoming_supplier.setStyleSheet(self._input_style())
        form_layout.addRow("Поставщик:", self.incoming_supplier)
        
        self.incoming_doc_number = QLineEdit()
        self.incoming_doc_number.setPlaceholderText("ПРИХ-001/2025")
        self.incoming_doc_number.setMinimumHeight(40)
        self.incoming_doc_number.setStyleSheet(self._input_style())
        form_layout.addRow("Документ:", self.incoming_doc_number)
        
        self.incoming_doc_date = QDateEdit()
        self.incoming_doc_date.setCalendarPopup(True)
        self.incoming_doc_date.setDate(QDate.currentDate())
        self.incoming_doc_date.setMinimumHeight(40)
        self.incoming_doc_date.setStyleSheet(self._input_style())
        form_layout.addRow("Дата:", self.incoming_doc_date)
        
        self.incoming_notes = QTextEdit()
        self.incoming_notes.setPlaceholderText("Примечание...")
        self.incoming_notes.setMaximumHeight(60)
        self.incoming_notes.setStyleSheet(self._input_style())
        form_layout.addRow("Примечание:", self.incoming_notes)
        
        add_btn = QPushButton("✅ Провести приход")
        add_btn.setFixedHeight(45)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
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
        add_btn.clicked.connect(self.add_incoming)
        form_layout.addRow(add_btn)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
    def setup_outgoing_tab(self):
        layout = QVBoxLayout(self.outgoing_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Индикация запасов
        self.outgoing_indicator_label = QLabel("📊 Текущие запасы материалов:")
        self.outgoing_indicator_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.outgoing_indicator_label.setStyleSheet("color: #2C3E50;")
        layout.addWidget(self.outgoing_indicator_label)
        
        self.outgoing_indicator_table = QTableWidget()
        self.outgoing_indicator_table.setColumnCount(5)
        self.outgoing_indicator_table.setHorizontalHeaderLabels([
            "Материал", "Категория", "Остаток", "Мин. запас", "Статус"
        ])
        self.outgoing_indicator_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.outgoing_indicator_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.outgoing_indicator_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.outgoing_indicator_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
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
        
        # Форма расхода
        form_group = self._create_group_box("➖ Списать материал", self.OUTGOING_COLOR)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        
        self.outgoing_material = QComboBox()
        self.outgoing_material.setMinimumHeight(40)
        self.outgoing_material.setStyleSheet(self._input_style())
        self.outgoing_material.currentIndexChanged.connect(self.on_outgoing_material_changed)
        form_layout.addRow("Материал:", self.outgoing_material)
        
        self.outgoing_available = QLabel("Доступно: 0 шт")
        self.outgoing_available.setStyleSheet("font-weight: bold; color: #7F8C8D; padding: 8px;")
        form_layout.addRow("Доступно:", self.outgoing_available)
        
        self.outgoing_quantity = QLineEdit()
        self.outgoing_quantity.setPlaceholderText("Количество")
        self.outgoing_quantity.setMinimumHeight(40)
        self.outgoing_quantity.setStyleSheet(self._input_style())
        form_layout.addRow("Количество:", self.outgoing_quantity)
        
        self.outgoing_doc_number = QLineEdit()
        self.outgoing_doc_number.setPlaceholderText("РАСХ-015/2025")
        self.outgoing_doc_number.setMinimumHeight(40)
        self.outgoing_doc_number.setStyleSheet(self._input_style())
        form_layout.addRow("Документ:", self.outgoing_doc_number)
        
        self.outgoing_doc_date = QDateEdit()
        self.outgoing_doc_date.setCalendarPopup(True)
        self.outgoing_doc_date.setDate(QDate.currentDate())
        self.outgoing_doc_date.setMinimumHeight(40)
        self.outgoing_doc_date.setStyleSheet(self._input_style())
        form_layout.addRow("Дата:", self.outgoing_doc_date)
        
        self.outgoing_notes = QTextEdit()
        self.outgoing_notes.setPlaceholderText("Примечание...")
        self.outgoing_notes.setMaximumHeight(60)
        self.outgoing_notes.setStyleSheet(self._input_style())
        form_layout.addRow("Примечание:", self.outgoing_notes)
        
        add_btn = QPushButton("❌ Провести расход")
        add_btn.setFixedHeight(45)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
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
        add_btn.clicked.connect(self.add_outgoing)
        form_layout.addRow(add_btn)
        
        layout.addWidget(form_group)
        layout.addStretch()

    def setup_materials_info_tab(self):
        layout = QVBoxLayout(self.materials_info_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header_layout = QHBoxLayout()
        title = QLabel("📋 Полный список материалов")
        title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.PRIMARY_COLOR};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setFixedSize(100, 32)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY_COLOR};
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_DARK};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_materials_info)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(8)
        self.materials_table.setHorizontalHeaderLabels([
            "ID", "Наименование", "Категория", "Остаток", "Ед.", "Мин. запас", "Цена (₽)", "Поставщик"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.materials_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.materials_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #1A529C;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(self.materials_table, 1)

    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header_layout = QHBoxLayout()
        title = QLabel("📜 Журнал приходов и расходов")
        title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.PRIMARY_COLOR};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setFixedSize(100, 32)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY_COLOR};
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_DARK};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_history)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Дата", "Материал", "Тип", "Кол-во", "Документ", "Пользователь", "Примечание"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(self.history_table, 1)
        
    def _create_group_box(self, title: str, color: str) -> QGroupBox:
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
        try:
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
            
            self.incoming_material.clear()
            self.outgoing_material.clear()
            for mat in self.materials_cache:
                mat_id, name, qty, unit, min_qty, category = mat
                display_text = f"{name} ({category or 'Без категории'}) - {qty} {unit}"
                self.incoming_material.addItem(display_text, mat_id)
                self.outgoing_material.addItem(display_text, mat_id)
            
            suppliers_query = """
                SELECT DISTINCT supplier
                FROM materials
                WHERE supplier IS NOT NULL AND supplier != ''
                ORDER BY supplier
            """
            cursor = conn.cursor()
            cursor.execute(suppliers_query)
            self.suppliers_cache = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            self.incoming_supplier.addItems(self.suppliers_cache)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить списки: {str(e)}")
            
    def refresh_all_data(self):
        """Обновляет данные на всех вкладках"""
        self.refresh_materials_indicator()
        self.refresh_materials_info()
        self.refresh_history()
            
    def refresh_materials_indicator(self):
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
            
            for table in [self.incoming_indicator_table, self.outgoing_indicator_table]:
                table.setRowCount(len(materials))
                for row_idx, mat in enumerate(materials):
                    mat_id, name, qty, min_qty, unit, category = mat
                    
                    if qty == 0:
                        status = "⚫ Нет в наличии"
                        color = "#2C3E50"
                        bg = "#F5F5F5"
                    elif qty <= min_qty:
                        pct = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🔴 Критично ({pct:.0f}%)"
                        color = "#E74C3C"
                        bg = "#FADBD8"
                    elif qty <= min_qty * 1.5:
                        pct = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🟡 Заканчивается ({pct:.0f}%)"
                        color = "#F39C12"
                        bg = "#FDEBD0"
                    else:
                        pct = (qty / min_qty * 100) if min_qty > 0 else 0
                        status = f"🟢 В достатке ({pct:.0f}%)"
                        color = "#27AE60"
                        bg = "#D5F5E3"
                    
                    table.setItem(row_idx, 0, QTableWidgetItem(name))
                    table.setItem(row_idx, 1, QTableWidgetItem(category or "Без категории"))
                    table.setItem(row_idx, 2, QTableWidgetItem(f"{qty} {unit}"))
                    table.setItem(row_idx, 3, QTableWidgetItem(f"{min_qty} {unit}"))
                    
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(QColor(color))
                    table.setItem(row_idx, 4, status_item)
                    
                    for col in range(5):
                        item = table.item(row_idx, col)
                        if item:
                            item.setBackground(QColor(bg))
        except Exception as e:
            print(f"Ошибка индикации: {e}")

    def refresh_materials_info(self):
        try:
            query = """
                SELECT m.id, m.name, c.name as category_name, m.quantity, m.unit, 
                       m.min_quantity, m.price, m.supplier
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
            
            self.materials_table.setRowCount(len(materials))
            for row_idx, mat in enumerate(materials):
                mat_id, name, cat, qty, unit, min_qty, price, supplier = mat
                self.materials_table.setItem(row_idx, 0, QTableWidgetItem(str(mat_id)))
                self.materials_table.setItem(row_idx, 1, QTableWidgetItem(name))
                self.materials_table.setItem(row_idx, 2, QTableWidgetItem(cat or "Без категории"))
                self.materials_table.setItem(row_idx, 3, QTableWidgetItem(str(qty)))
                self.materials_table.setItem(row_idx, 4, QTableWidgetItem(unit))
                self.materials_table.setItem(row_idx, 5, QTableWidgetItem(str(min_qty)))
                self.materials_table.setItem(row_idx, 6, QTableWidgetItem(f"{price:.2f}" if price else "0.00"))
                self.materials_table.setItem(row_idx, 7, QTableWidgetItem(supplier or "Не указан"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить материалы: {str(e)}")

    def refresh_history(self):
        try:
            query = """
                SELECT t.document_date, m.name as material_name, t.transaction_type, 
                       t.quantity, t.document_number, u.full_name as user_name, t.notes
                FROM transactions t
                LEFT JOIN materials m ON t.material_id = m.id
                LEFT JOIN users u ON t.user_id = u.id
                ORDER BY t.created_at DESC
            """
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            history = cursor.fetchall()
            cursor.close()
            conn.close()
            
            self.history_table.setRowCount(len(history))
            for row_idx, rec in enumerate(history):
                date, mat_name, type_, qty, doc, user, notes = rec
                
                type_text = "📥 Приход" if type_ == 'incoming' else "📤 Расход"
                type_color = "#27AE60" if type_ == 'incoming' else "#E74C3C"
                
                self.history_table.setItem(row_idx, 0, QTableWidgetItem(
                    date.strftime("%d.%m.%Y") if date else ""
                ))
                self.history_table.setItem(row_idx, 1, QTableWidgetItem(mat_name or "Удалён"))
                
                type_item = QTableWidgetItem(type_text)
                type_item.setForeground(QColor(type_color))
                self.history_table.setItem(row_idx, 2, type_item)
                
                self.history_table.setItem(row_idx, 3, QTableWidgetItem(str(qty)))
                self.history_table.setItem(row_idx, 4, QTableWidgetItem(doc or "-"))
                self.history_table.setItem(row_idx, 5, QTableWidgetItem(user or "Система"))
                self.history_table.setItem(row_idx, 6, QTableWidgetItem(notes or ""))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {str(e)}")
            
    def on_outgoing_material_changed(self, index):
        if index >= 0 and index < len(self.materials_cache):
            mat = self.materials_cache[index]
            mat_id, name, qty, unit, min_qty, category = mat
            self.outgoing_available.setText(f"Доступно: {qty} {unit}")
            
    def add_incoming(self):
        try:
            idx = self.incoming_material.currentIndex()
            if idx < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите материал!")
                return
            mat_id = self.incoming_material.itemData(idx)
            qty_str = self.incoming_quantity.text().strip()
            supplier = self.incoming_supplier.currentText().strip()
            doc_num = self.incoming_doc_number.text().strip()
            doc_date = self.incoming_doc_date.date().toPython()
            notes = self.incoming_notes.toPlainText().strip()
            
            if not qty_str or not doc_num:
                QMessageBox.warning(self, "Ошибка", "Заполните количество и номер документа!")
                return
                
            try:
                quantity = int(qty_str)
            except:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть числом!")
                return
            if quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0!")
                return
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM materials WHERE id = %s", (mat_id,))
            res = cursor.fetchone()
            if not res:
                QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                cursor.close()
                conn.close()
                return
            
            new_qty = res[0] + quantity
            try:
                cursor.execute(
                    "UPDATE materials SET quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_qty, mat_id)
                )
                cursor.execute("""
                    INSERT INTO transactions 
                    (material_id, user_id, quantity, transaction_type, document_number, document_date, notes)
                    VALUES (%s, %s, %s, 'incoming', %s, %s, %s)
                """, (mat_id, self.user_data['id'], quantity, doc_num, doc_date, notes))
                conn.commit()
                
                QMessageBox.information(
                    self, "Успешно",
                    f"Приход проведён!\n"
                    f"Материал: {self.incoming_material.currentText()}\n"
                    f"Количество: +{quantity}\n"
                    f"Новый остаток: {new_qty}"
                )
                
                self.incoming_quantity.clear()
                self.incoming_doc_number.clear()
                self.incoming_notes.clear()
                self.load_combo_data()
                self.refresh_all_data()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка прихода: {str(e)}")
            
    def add_outgoing(self):
        try:
            idx = self.outgoing_material.currentIndex()
            if idx < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите материал!")
                return
            mat_id = self.outgoing_material.itemData(idx)
            qty_str = self.outgoing_quantity.text().strip()
            doc_num = self.outgoing_doc_number.text().strip()
            doc_date = self.outgoing_doc_date.date().toPython()
            notes = self.outgoing_notes.toPlainText().strip()
            
            if not qty_str or not doc_num:
                QMessageBox.warning(self, "Ошибка", "Заполните количество и номер документа!")
                return
                
            try:
                quantity = int(qty_str)
            except:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть числом!")
                return
            if quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0!")
                return
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM materials WHERE id = %s", (mat_id,))
            res = cursor.fetchone()
            if not res:
                QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                cursor.close()
                conn.close()
                return
            
            if quantity > res[0]:
                QMessageBox.warning(
                    self, "Недостаточно материала",
                    f"Доступно: {res[0]} шт\n"
                    f"Вы пытаетесь списать: {quantity} шт\n\n"
                    f"Нельзя уйти в минус!"
                )
                cursor.close()
                conn.close()
                return
            
            new_qty = res[0] - quantity
            try:
                cursor.execute(
                    "UPDATE materials SET quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_qty, mat_id)
                )
                cursor.execute("""
                    INSERT INTO transactions 
                    (material_id, user_id, quantity, transaction_type, document_number, document_date, notes)
                    VALUES (%s, %s, %s, 'outgoing', %s, %s, %s)
                """, (mat_id, self.user_data['id'], quantity, doc_num, doc_date, notes))
                conn.commit()
                
                QMessageBox.information(
                    self, "Успешно",
                    f"Расход проведён!\n"
                    f"Материал: {self.outgoing_material.currentText()}\n"
                    f"Количество: -{quantity}\n"
                    f"Новый остаток: {new_qty}"
                )
                
                self.outgoing_quantity.clear()
                self.outgoing_doc_number.clear()
                self.outgoing_notes.clear()
                self.load_combo_data()
                self.refresh_all_data()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расхода: {str(e)}")
            
    def go_back(self):
        self.back_to_table.emit()
        self.close()
        
    def logout(self):
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()