# views/reports_page.py
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QGroupBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from database import Database
from datetime import datetime, date

# Попытка импорта графиков
try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ReportsPage(QMainWindow):
    back_to_table = Signal()
    
    # Цвета
    PRIMARY_COLOR = "#1A529C"
    PRIMARY_DARK = "#0d47a1"
    PRIMARY_LIGHT = "#E3F2FD"
    SUCCESS_COLOR = "#27AE60"
    WARNING_COLOR = "#F39C12"
    DANGER_COLOR = "#E74C3C"
    INFO_COLOR = "#3498DB"
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = Database()
        self.init_ui()
        self.load_dashboard_data()
        if HAS_MATPLOTLIB:
            self.load_charts_data()
        self.load_critical_stock_data()
        
    def init_ui(self):
        self.setWindowTitle(f"Отчёты по стройкам | {self.user_data['full_name']}")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 750)
        
        central = QWidget()
        central.setStyleSheet("background-color: white;")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ─── Верхняя панель ──────────────────────────────────────
        top_panel = QWidget()
        top_panel.setFixedHeight(60)
        top_panel.setStyleSheet(f"background: {self.PRIMARY_LIGHT}; border-bottom: 2px solid {self.PRIMARY_COLOR};")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 20, 0)
        
        back_btn = QPushButton("← Назад к таблицам")
        back_btn.setFixedSize(180, 36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.PRIMARY_COLOR}; color: white; border: none; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background: {self.PRIMARY_DARK}; }}
        """)
        back_btn.clicked.connect(self.go_back)
        top_layout.addWidget(back_btn)
        
        title = QLabel("📊 Отчёты и аналитика склада")
        title.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.PRIMARY_COLOR};")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        logout_btn = QPushButton("Выйти")
        logout_btn.setFixedSize(80, 32)
        logout_btn.setStyleSheet("""
            QPushButton { background: #6C757D; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background: #5A6268; }
        """)
        logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(logout_btn)
        
        main_layout.addWidget(top_panel)
        
        # ─── Вкладки ─────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.PRIMARY_COLOR}; background: #FAFAFA; }}
            QTabBar::tab {{ background: {self.PRIMARY_LIGHT}; color: {self.PRIMARY_COLOR};
                padding: 10px 24px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px;
                font-weight: bold; font-size: 13px; }}
            QTabBar::tab:selected {{ background: white; border-bottom: 2px solid white; }}
            QTabBar::tab:hover:!selected {{ background: #D6EAF8; }}
        """)
        
        # Вкладка 1: Сводка
        self.dashboard_tab = QWidget()
        self.dashboard_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📋 Сводка")
        
        # Вкладка 2: Графики
        self.charts_tab = QWidget()
        self.charts_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_charts_tab()
        self.tabs.addTab(self.charts_tab, "📈 Графики")
        
        # Вкладка 3: Критический остаток
        self.stock_tab = QWidget()
        self.stock_tab.setStyleSheet("background-color: #FAFAFA;")
        self.setup_stock_tab()
        self.tabs.addTab(self.stock_tab, "⚠️ Внимание (Мало)")
        
        self.tabs.setCurrentIndex(0)
        main_layout.addWidget(self.tabs, 1)
        
    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header = QLabel("📋 Ключевые показатели")
        header.setFont(QFont('Segoe UI', 15, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {self.PRIMARY_COLOR};")
        layout.addWidget(header)
        
        # Сетка карточек
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        self.cards = {}
        card_configs = [
            ("💰 Общая стоимость", "total_value", self.PRIMARY_COLOR),
            ("📦 Всего позиций", "total_items", self.INFO_COLOR),
            ("📥 Приходов (мес)", "incoming_month", self.SUCCESS_COLOR),
            ("📤 Расходов (мес)", "outgoing_month", self.DANGER_COLOR),
            ("⚠️ Заканчивается", "low_stock", self.WARNING_COLOR),
            ("🚫 Нет в наличии", "zero_stock", "#7F8C8D"),
        ]
        
        for i, (title, key, color) in enumerate(card_configs):
            card = self._create_card(title, "Загрузка...", color)
            self.cards[key] = card["value_label"]
            cards_layout.addWidget(card["frame"], i // 3, i % 3)
            
        layout.addLayout(cards_layout)
        layout.addStretch()
        
    def setup_charts_tab(self):
        layout = QVBoxLayout(self.charts_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        if not HAS_MATPLOTLIB:
            msg = QLabel("⚠️ Для отображения графиков установите библиотеку: <b>pip install matplotlib</b>")
            msg.setWordWrap(True)
            msg.setFont(QFont('Segoe UI', 12))
            msg.setStyleSheet("color: #E74C3C; padding: 20px;")
            layout.addWidget(msg)
            layout.addStretch()
            return
            
        # График приходов/расходов
        flow_group = QGroupBox("📈 Динамика приходов и расходов")
        flow_group.setStyleSheet(self._group_box_style())
        flow_layout = QVBoxLayout(flow_group)
        self.flow_canvas = self._create_matplotlib_canvas()
        flow_layout.addWidget(self.flow_canvas)
        layout.addWidget(flow_group)
        
        # График категорий
        cat_group = QGroupBox("🥧 Распределение стоимости по категориям")
        cat_group.setStyleSheet(self._group_box_style())
        cat_layout = QVBoxLayout(cat_group)
        self.cat_canvas = self._create_matplotlib_canvas()
        self.cat_placeholder = QLabel()
        self.cat_placeholder.setAlignment(Qt.AlignCenter)
        self.cat_placeholder.setStyleSheet("""
            QLabel { 
                color: #7F8C8D; 
                font-size: 14px; 
                padding: 40px;
                background: #FAFAFA;
                border: 2px dashed #BDC3C7;
                border-radius: 8px;
            }
        """)
        cat_layout.addWidget(self.cat_canvas)
        cat_layout.addWidget(self.cat_placeholder)
        layout.addWidget(cat_group, 1)
        
    def setup_stock_tab(self):
        layout = QVBoxLayout(self.stock_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        header = QLabel("⚠️ Материалы с критическим остатком")
        header.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {self.WARNING_COLOR};")
        layout.addWidget(header)
        
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(5)
        self.low_stock_table.setHorizontalHeaderLabels([
            "Наименование", "Категория", "Текущий остаток", "Мин. запас", "Статус"
        ])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.low_stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_stock_table.setStyleSheet("""
            QTableWidget { background: white; border: 1px solid #E0E0E0; border-radius: 4px; }
            QHeaderView::section { background: #E74C3C; color: white; font-weight: bold; padding: 8px; border: none; }
        """)
        layout.addWidget(self.low_stock_table)
        layout.addStretch()

    # ─── Вспомогательные UI методы ───────────────────────────────
    def _create_card(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ background: white; border-left: 4px solid {color}; border-radius: 6px; padding: 15px; }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; color: #555; font-weight: 500;")
        layout.addWidget(title_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        value_lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(value_lbl)
        
        return {"frame": frame, "value_label": value_lbl}
        
    def _group_box_style(self):
        return f"""
            QGroupBox {{ font-weight: bold; font-size: 14px; color: {self.PRIMARY_COLOR};
                border: 2px solid {self.PRIMARY_COLOR}; border-radius: 8px; margin-top: 10px; padding-top: 10px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 8px; }}
        """
        
    def _create_matplotlib_canvas(self):
        fig = Figure(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('#FAFAFA')
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background: transparent;")
        return canvas

    # ─── Загрузка данных ─────────────────────────────────────────
    def load_dashboard_data(self):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 1. Общая стоимость и кол-во
            cursor.execute("SELECT COALESCE(SUM(quantity * price), 0), COUNT(*) FROM materials")
            total_val, total_cnt = cursor.fetchone()
            self.cards["total_value"].setText(f"{total_val:,.0f} ₽")
            self.cards["total_items"].setText(str(total_cnt))
            
            # 2. Низкий и нулевой запас
            cursor.execute("SELECT COUNT(*) FROM materials WHERE quantity <= min_quantity AND quantity > 0")
            low = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM materials WHERE quantity = 0")
            zero = cursor.fetchone()[0]
            self.cards["low_stock"].setText(str(low))
            self.cards["zero_stock"].setText(str(zero))
            
            # 3. Приходы/Расходы за текущий месяц
            first_day = datetime.now().replace(day=1).date()
            cursor.execute("""
                SELECT transaction_type, COALESCE(SUM(quantity), 0)
                FROM transactions WHERE document_date >= %s GROUP BY transaction_type
            """, (first_day,))
            month_data = {row[0]: row[1] for row in cursor.fetchall()}
            self.cards["incoming_month"].setText(f"+{month_data.get('incoming', 0)}")
            self.cards["outgoing_month"].setText(f"-{month_data.get('outgoing', 0)}")
            
            cursor.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось загрузить дашборд: {e}")
            
    def load_charts_data(self):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Получаем текущую дату
            today = date.today()
            
            # Данные за последние 30 дней (по дням), но не дальше текущей даты
            cursor.execute("""
                SELECT DATE(document_date) as day, transaction_type, COALESCE(SUM(quantity), 0)
                FROM transactions
                WHERE document_date >= CURRENT_DATE - INTERVAL '30 days'
                AND document_date <= CURRENT_DATE
                GROUP BY day, transaction_type 
                ORDER BY day
            """)
            rows = cursor.fetchall()
            
            days = []
            incoming = []
            outgoing = []
            
            if rows:
                # Создаем словарь для удобного доступа
                data_dict = {}
                for day, t, q in rows:
                    # Фильтруем даты - показываем только до сегодня включительно
                    if day <= today:
                        day_str = day.strftime("%d.%m")
                        if day_str not in data_dict:
                            data_dict[day_str] = {'incoming': 0, 'outgoing': 0}
                        data_dict[day_str][t] = q
                
                # Преобразуем в списки для графика
                days = sorted(data_dict.keys())
                incoming = [data_dict[d]['incoming'] for d in days]
                outgoing = [data_dict[d]['outgoing'] for d in days]
                
                # Очищаем и рисуем график
                self.flow_canvas.figure.clear()
                ax1 = self.flow_canvas.figure.subplots()
                
                x = range(len(days))
                ax1.plot(x, incoming, marker='o', color=self.SUCCESS_COLOR, label='Приход', linewidth=2)
                ax1.plot(x, outgoing, marker='s', color=self.DANGER_COLOR, label='Расход', linewidth=2)
                
                ax1.set_title("Движение материалов (последние 30 дней)", fontsize=12, fontweight='bold')
                ax1.set_xticks(x)
                ax1.set_xticklabels(days, rotation=45, ha='right')
                ax1.legend(loc='upper right')
                ax1.grid(True, linestyle='--', alpha=0.5)
                ax1.set_ylabel('Количество')
                
                # Добавляем подписи значений на график
                for i, (inc, out) in enumerate(zip(incoming, outgoing)):
                    if inc > 0:
                        ax1.annotate(f'{inc}', (i, inc), textcoords="offset points", xytext=(0,5), ha='center', fontsize=8)
                    if out > 0:
                        ax1.annotate(f'{out}', (i, out), textcoords="offset points", xytext=(0,-10), ha='center', fontsize=8)
                
                self.flow_canvas.figure.tight_layout()
                self.flow_canvas.draw()
            else:
                # Если нет данных за 30 дней
                self.flow_canvas.figure.clear()
                ax1 = self.flow_canvas.figure.subplots()
                ax1.text(0.5, 0.5, 'Нет данных за последние 30 дней', 
                        ha='center', va='center', transform=ax1.transAxes, fontsize=12)
                ax1.axis('off')
                self.flow_canvas.draw()
            
            # ✅ График 2: Категории - ИСПРАВЛЕННЫЙ ЗАПРОС
            # Используем подзапрос, чтобы избежать ошибки с алиасом в HAVING
            cursor.execute("""
                SELECT name, total_val
                FROM (
                    SELECT c.name, COALESCE(SUM(m.quantity * m.price), 0) as total_val
                    FROM categories c 
                    LEFT JOIN materials m ON m.category_id = c.id
                    GROUP BY c.id, c.name
                ) as subquery
                WHERE total_val > 0
                ORDER BY total_val DESC
            """)
            cat_data = cursor.fetchall()
            
            # Очищаем фигуру перед рисованием
            self.cat_canvas.figure.clear()
            
            if cat_data:
                labels = [c[0] or "Другое" for c in cat_data]
                sizes = [c[1] for c in cat_data]
                
                ax2 = self.cat_canvas.figure.subplots()
                # Красивые цвета для диаграммы
                colors = ['#3498DB', '#2ECC71', '#E74C3C', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E']
                ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)])
                ax2.set_title("Стоимость по категориям", fontsize=12, fontweight='bold')
                self.cat_canvas.draw()
                self.cat_placeholder.hide()
            else:
                ax2 = self.cat_canvas.figure.subplots()
                ax2.axis('off')
                self.cat_placeholder.setText("📊 Нет данных для отображения\n\nДобавьте материалы с указанием категории и цены")
                self.cat_placeholder.show()
                
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Ошибка графиков: {e}")
            import traceback
            traceback.print_exc()
            
    def load_critical_stock_data(self):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.name, c.name, m.quantity, m.unit, m.min_quantity
                FROM materials m LEFT JOIN categories c ON m.category_id = c.id
                WHERE m.quantity <= m.min_quantity OR m.quantity = 0
                ORDER BY m.quantity ASC
            """)
            items = cursor.fetchall()
            cursor.close()
            conn.close()
            
            self.low_stock_table.setRowCount(len(items))
            for i, (name, cat, qty, unit, min_q) in enumerate(items):
                self.low_stock_table.setItem(i, 0, QTableWidgetItem(name))
                self.low_stock_table.setItem(i, 1, QTableWidgetItem(cat or "Без категории"))
                self.low_stock_table.setItem(i, 2, QTableWidgetItem(str(qty) + " " + unit))
                self.low_stock_table.setItem(i, 3, QTableWidgetItem(str(min_q)))
                
                status = "🚫 Нет" if qty == 0 else f"⚠️ Мало ({qty}/{min_q})"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(self.DANGER_COLOR if qty == 0 else self.WARNING_COLOR))
                self.low_stock_table.setItem(i, 4, status_item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить запасы: {e}")

    def go_back(self):
        self.back_to_table.emit()
        self.close()
        
    def logout(self):
        self.close()
        from .main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()