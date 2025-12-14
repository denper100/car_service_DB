import sys
import psycopg2
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

class SimpleDBApp:
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.window.setWindowTitle("Автосервис - Управление БД")
        self.window.setGeometry(100, 100, 1000, 600)
        
        # Подключение к БД
        self.conn = None
        self.connect_db()
        
        self.setup_ui()
        
    def connect_db(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="car_service",
                user="postgres",
                password="postgres",  
                port="5432"
            )
            print("Успешное подключение к БД")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            QMessageBox.critical(None, "Ошибка", 
                f"Не удалось подключиться к БД:\n{str(e)}")
            sys.exit(1)
    
    def setup_ui(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Верхняя панель
        top_panel = QHBoxLayout()
        
        self.table_combo = QComboBox()
        self.table_combo.addItems([
            "cars - Автомобили",
            "workshops - Цеха", 
            "teams - Бригады",
            "personnel - Персонал",
            "faults - Неисправности",
            "car_repair - Ремонты",
            "spare_parts - Запчасти"
        ])
        self.table_combo.currentIndexChanged.connect(self.load_table)
        
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_table)
        
        add_btn = QPushButton("+ Добавить")
        add_btn.clicked.connect(self.add_record)
        
        edit_btn = QPushButton("✎ Редактировать")
        edit_btn.clicked.connect(self.edit_record)
        
        delete_btn = QPushButton("🗑 Удалить")
        delete_btn.clicked.connect(self.delete_record)
        
        top_panel.addWidget(QLabel("Таблица:"))
        top_panel.addWidget(self.table_combo)
        top_panel.addWidget(refresh_btn)
        top_panel.addWidget(add_btn)
        top_panel.addWidget(edit_btn)
        top_panel.addWidget(delete_btn)
        
        layout.addLayout(top_panel)
        
        # Панель поиска и фильтрации
        filter_panel = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по всем полям...")
        self.search_input.textChanged.connect(self.search_data)
        
        self.filter_field = QComboBox()
        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("Значение для фильтра")
        filter_btn = QPushButton("Фильтровать")
        filter_btn.clicked.connect(self.apply_filter)
        
        clear_btn = QPushButton("Сбросить фильтры")
        clear_btn.clicked.connect(self.clear_filters)
        
        filter_panel.addWidget(QLabel("Поиск:"))
        filter_panel.addWidget(self.search_input)
        filter_panel.addWidget(QLabel("Поле:"))
        filter_panel.addWidget(self.filter_field)
        filter_panel.addWidget(self.filter_value)
        filter_panel.addWidget(filter_btn)
        filter_panel.addWidget(clear_btn)
        
        layout.addLayout(filter_panel)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.edit_record)
        layout.addWidget(self.table)
        
        # Нижняя панель
        bottom_panel = QHBoxLayout()
        
        self.status_label = QLabel("Готово")
        self.row_count_label = QLabel("Записей: 0")
        
        reports_btn = QPushButton("📊 Отчеты")
        reports_btn.clicked.connect(self.show_reports)
        
        complex_form_btn = QPushButton("➕ Сложная форма (ремонт+запчасти)")
        complex_form_btn.clicked.connect(self.complex_form)
        
        bottom_panel.addWidget(self.status_label)
        bottom_panel.addStretch()
        bottom_panel.addWidget(self.row_count_label)
        bottom_panel.addWidget(reports_btn)
        bottom_panel.addWidget(complex_form_btn)
        
        layout.addLayout(bottom_panel)
        
        # Загружаем первую таблицу
        self.current_table = ""
        self.current_data = []
        self.load_table()
        
    def get_table_name(self):
        """Получаем имя таблицы из комбобокса"""
        text = self.table_combo.currentText()
        return text.split(" - ")[0]
    
    def load_table(self):
        """Загрузка данных таблицы"""
        table_name = self.get_table_name()
        if table_name == self.current_table:
            return
            
        self.current_table = table_name
        
        try:
            # Получаем структуру таблицы
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # Заполняем комбобокс фильтров
            self.filter_field.clear()
            for col_name, col_type in columns:
                self.filter_field.addItem(col_name)
            
            # Загружаем данные
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1")
            self.current_data = cursor.fetchall()
            
            # Настраиваем таблицу
            self.table.setColumnCount(len(columns))
            self.table.setRowCount(len(self.current_data))
            
            # Заголовки
            headers = [col[0] for col in columns]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Данные
            for row_idx, row in enumerate(self.current_data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)
            
            self.table.resizeColumnsToContents()
            self.row_count_label.setText(f"Записей: {len(self.current_data)}")
            self.status_label.setText(f"Загружена таблица: {table_name}")
            
        except Exception as e:
            QMessageBox.critical(self.window, "Ошибка", f"Ошибка загрузки: {str(e)}")
    
    def search_data(self):
        """Поиск по всем полям"""
        search_text = self.search_input.text().lower()
        if not search_text:
            self.load_table()
            return
            
        for row in range(self.table.rowCount()):
            found = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    found = True
                    break
            self.table.setRowHidden(row, not found)
    
    def apply_filter(self):
        """Применение фильтра по выбранному полю"""
        field = self.filter_field.currentText()
        value = self.filter_value.text()
        
        if not field or not value:
            return
            
        try:
            cursor = self.conn.cursor()
            query = f"SELECT * FROM {self.current_table} WHERE {field}::text ILIKE %s ORDER BY 1"
            cursor.execute(query, (f'%{value}%',))
            
            data = cursor.fetchall()
            self.display_filtered_data(data)
            
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка фильтрации: {str(e)}")
    
    def display_filtered_data(self, data):
        """Отображение отфильтрованных данных"""
        self.table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
        
        self.row_count_label.setText(f"Записей (отфильтровано): {len(data)}")
    
    def clear_filters(self):
        """Сброс всех фильтров"""
        self.search_input.clear()
        self.filter_value.clear()
        self.load_table()
    
    def add_record(self):
        """Добавление новой записи"""
        self.show_edit_dialog()
    
    def edit_record(self):
        """Редактирование выбранной записи"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.window, "Предупреждение", "Выберите запись для редактирования")
            return
            
        self.show_edit_dialog(selected_row)
    
    def delete_record(self):
        """Удаление выбранной записи"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.window, "Предупреждение", "Выберите запись для удаления")
            return
            
        reply = QMessageBox.question(
            self.window, "Подтверждение",
            "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.conn.cursor()
                # Получаем имя первого столбца (обычно ID)
                pk_column = self.table.horizontalHeaderItem(0).text()
                pk_value = self.table.item(selected_row, 0).text()
                
                query = f"DELETE FROM {self.current_table} WHERE {pk_column} = %s"
                cursor.execute(query, (pk_value,))
                self.conn.commit()
                
                self.load_table()
                self.status_label.setText("Запись удалена")
                
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self.window, "Ошибка", f"Ошибка удаления: {str(e)}")
    
    def show_edit_dialog(self, row_idx=None):
        """Диалог добавления/редактирования записи"""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Добавить запись" if row_idx is None else "Редактировать запись")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Получаем информацию о столбцах
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = '{self.current_table}'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        # Создаем поля ввода
        inputs = {}
        form_layout = QFormLayout()
        
        for i, (col_name, col_type, is_nullable) in enumerate(columns):
            # Пропускаем автоинкрементные поля при добавлении
            if row_idx is None and "serial" in col_type:
                continue
                
            if "date" in col_type:
                input_widget = QDateEdit()
                input_widget.setCalendarPopup(True)
                input_widget.setDate(QDate.currentDate())
            elif "numeric" in col_type or "int" in col_type:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText("0")
            else:
                input_widget = QLineEdit()
            
            inputs[col_name] = input_widget
            form_layout.addRow(col_name, input_widget)
            
            # Заполняем данные при редактировании
            if row_idx is not None and i < len(self.current_data[row_idx]):
                value = self.current_data[row_idx][i]
                if value:
                    if isinstance(input_widget, QDateEdit):
                        try:
                            date = QDate.fromString(str(value), "yyyy-MM-dd")
                            input_widget.setDate(date)
                        except:
                            pass
                    else:
                        input_widget.setText(str(value))
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(lambda: self.save_record(dialog, inputs, columns, row_idx))
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.resize(400, 300)
        dialog.exec()
    
    def save_record(self, dialog, inputs, columns, row_idx):
        """Сохранение записи"""
        try:
            cursor = self.conn.cursor()
            
            if row_idx is None:
                # Добавление
                fields = []
                values = []
                placeholders = []
                
                for col_name, col_type, is_nullable in columns:
                    if col_name in inputs:
                        widget = inputs[col_name]
                        value = None
                        
                        if isinstance(widget, QDateEdit):
                            value = widget.date().toString("yyyy-MM-dd")
                        elif widget.text():
                            value = widget.text()
                        
                        if value is not None:
                            fields.append(col_name)
                            values.append(value)
                            placeholders.append("%s")
                
                if fields:
                    query = f"INSERT INTO {self.current_table} ({','.join(fields)}) VALUES ({','.join(placeholders)})"
                    cursor.execute(query, values)
                    
            else:
                # Редактирование
                pk_column = columns[0][0]
                pk_value = self.current_data[row_idx][0]
                
                set_clause = []
                values = []
                
                for col_name, col_type, is_nullable in columns:
                    if col_name in inputs and col_name != pk_column:
                        widget = inputs[col_name]
                        value = None
                        
                        if isinstance(widget, QDateEdit):
                            value = widget.date().toString("yyyy-MM-dd")
                        elif widget.text():
                            value = widget.text()
                        
                        if value is not None:
                            set_clause.append(f"{col_name} = %s")
                            values.append(value)
                
                if set_clause:
                    values.append(pk_value)
                    query = f"UPDATE {self.current_table} SET {', '.join(set_clause)} WHERE {pk_column} = %s"
                    cursor.execute(query, values)
            
            self.conn.commit()
            self.load_table()
            dialog.accept()
            self.status_label.setText("Запись сохранена")
            
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(dialog, "Ошибка", f"Ошибка сохранения: {str(e)}")
    
    def complex_form(self):
        """Сложная форма: ремонт + запчасти (1:М)"""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Добавление ремонта с запчастями")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Ремонт
        repair_tab = QWidget()
        repair_layout = QFormLayout(repair_tab)
        
        # Выбор автомобиля
        cursor = self.conn.cursor()
        cursor.execute("SELECT car_id, body_number, owner FROM cars ORDER BY owner")
        cars = cursor.fetchall()
        
        car_combo = QComboBox()
        for car_id, body_number, owner in cars:
            car_combo.addItem(f"{owner} ({body_number})", car_id)
        
        # Выбор неисправности
        cursor.execute("SELECT fault_id, name, work_cost FROM faults ORDER BY name")
        faults = cursor.fetchall()
        
        fault_combo = QComboBox()
        for fault_id, name, cost in faults:
            fault_combo.addItem(f"{name} ({cost} руб.)", fault_id)
        
        # Даты
        admission_date = QDateEdit()
        admission_date.setDate(QDate.currentDate())
        admission_date.setCalendarPopup(True)
        
        completion_date = QDateEdit()
        completion_date.setDate(QDate.currentDate().addDays(1))
        completion_date.setCalendarPopup(True)
        
        # Выбор бригады
        cursor.execute("SELECT team_id, name FROM teams ORDER BY name")
        teams = cursor.fetchall()
        
        team_combo = QComboBox()
        team_combo.addItem("Не назначена", None)
        for team_id, name in teams:
            team_combo.addItem(name, team_id)
        
        repair_layout.addRow("Автомобиль:", car_combo)
        repair_layout.addRow("Неисправность:", fault_combo)
        repair_layout.addRow("Дата поступления:", admission_date)
        repair_layout.addRow("Дата завершения:", completion_date)
        repair_layout.addRow("Бригада:", team_combo)
        
        # Вкладка 2: Запчасти
        parts_tab = QWidget()
        parts_layout = QVBoxLayout(parts_tab)
        
        # Таблица запчастей
        parts_table = QTableWidget()
        parts_table.setColumnCount(3)
        parts_table.setHorizontalHeaderLabels(["Название", "Цена", "Количество"])
        parts_layout.addWidget(parts_table)
        
        # Кнопки управления запчастями
        parts_buttons = QHBoxLayout()
        add_part_btn = QPushButton("+ Добавить запчасть")
        remove_part_btn = QPushButton("- Удалить запчасть")
        
        parts_buttons.addWidget(add_part_btn)
        parts_buttons.addWidget(remove_part_btn)
        parts_buttons.addStretch()
        parts_layout.addLayout(parts_buttons)
        
        def add_part():
            row = parts_table.rowCount()
            parts_table.insertRow(row)
            parts_table.setItem(row, 0, QTableWidgetItem(""))
            parts_table.setItem(row, 1, QTableWidgetItem("0"))
            parts_table.setItem(row, 2, QTableWidgetItem("1"))
        
        def remove_part():
            current = parts_table.currentRow()
            if current >= 0:
                parts_table.removeRow(current)
        
        add_part_btn.clicked.connect(add_part)
        remove_part_btn.clicked.connect(remove_part)
        
        # Добавляем одну запчасть по умолчанию
        add_part()
        
        tabs.addTab(repair_tab, "Информация о ремонте")
        tabs.addTab(parts_tab, "Запчасти")
        
        layout.addWidget(tabs)
        
        # Кнопки сохранения
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        def save_complex():
            try:
                cursor = self.conn.cursor()
                
                # 1. Сохраняем ремонт
                car_id = car_combo.currentData()
                fault_id = fault_combo.currentData()
                admission = admission_date.date().toString("yyyy-MM-dd")
                completion = completion_date.date().toString("yyyy-MM-dd")
                team_id = team_combo.currentData()
                
                query = """
                    INSERT INTO car_repair 
                    (car_id, fault_id, admission_date, completion_date, team_id)
                    VALUES (%s, %s, %s, %s, %s) RETURNING repair_id
                """
                
                cursor.execute(query, (car_id, fault_id, admission, completion, team_id))
                # repair_id = cursor.fetchone()[0]
                
                # 2. Сохраняем запчасти
                for row in range(parts_table.rowCount()):
                    name = parts_table.item(row, 0).text()
                    price = parts_table.item(row, 1).text()
                    quantity = parts_table.item(row, 2).text()
                    
                    if name and price and quantity:
                        query = """
                            INSERT INTO spare_parts 
                            (car_id, fault_id, name, price, quantity)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(query, (car_id, fault_id, name, price, quantity))
                
                self.conn.commit()
                self.load_table()
                dialog.accept()
                self.status_label.setText("Ремонт с запчастями сохранен")
                
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка сохранения: {str(e)}")
        
        button_box.accepted.connect(save_complex)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.exec()
    
    def show_reports(self):
        """Показ отчетов"""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Отчеты")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Выбор отчета
        report_combo = QComboBox()
        report_combo.addItems([
            "1. Ремонты по датам",
            "2. Бригады и персонал", 
            "3. Финансовый отчет"
        ])
        
        layout.addWidget(QLabel("Выберите отчет:"))
        layout.addWidget(report_combo)
        
        # Параметры отчета
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        
        # Общие параметры
        start_date = QDateEdit()
        start_date.setDate(QDate.currentDate().addMonths(-1))
        start_date.setCalendarPopup(True)
        
        end_date = QDateEdit()
        end_date.setDate(QDate.currentDate())
        end_date.setCalendarPopup(True)
        
        params_layout.addWidget(QLabel("Начальная дата:"))
        params_layout.addWidget(start_date)
        params_layout.addWidget(QLabel("Конечная дата:"))
        params_layout.addWidget(end_date)
        
        layout.addWidget(params_widget)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        def generate_report():
            try:
                report_type = report_combo.currentIndex()
                
                if report_type == 0:  # Ремонты по датам
                    query = """
                        SELECT 
                            cr.admission_date,
                            c.owner,
                            c.body_number,
                            f.name,
                            f.work_cost,
                            COALESCE(SUM(sp.price * sp.quantity), 0) as parts_cost,
                            f.work_cost + COALESCE(SUM(sp.price * sp.quantity), 0) as total_cost
                        FROM car_repair cr
                        JOIN cars c ON cr.car_id = c.car_id
                        JOIN faults f ON cr.fault_id = f.fault_id
                        LEFT JOIN spare_parts sp ON cr.car_id = sp.car_id AND cr.fault_id = sp.fault_id
                        WHERE cr.admission_date BETWEEN %s AND %s
                        GROUP BY cr.admission_date, c.owner, c.body_number, f.name, f.work_cost
                        ORDER BY cr.admission_date
                    """
                    
                elif report_type == 1:  # Бригады и персонал
                    query = """
                        SELECT 
                            t.name as team_name,
                            COUNT(p.inn) as person_count,
                            w.name as workshop_name,
                            STRING_AGG(p.inn, ', ') as inn_list
                        FROM teams t
                        LEFT JOIN personnel p ON t.team_id = p.team_id
                        LEFT JOIN workshops w ON p.workshop_id = w.workshop_id
                        GROUP BY t.team_id, t.name, w.name
                        ORDER BY person_count DESC
                    """
                    
                else:  # Финансовый отчет
                    query = """
                        SELECT 
                            TO_CHAR(cr.admission_date, 'YYYY-MM') as month,
                            COUNT(*) as repair_count,
                            SUM(f.work_cost) as work_total,
                            COALESCE(SUM(sp.price * sp.quantity), 0) as parts_total,
                            SUM(f.work_cost) + COALESCE(SUM(sp.price * sp.quantity), 0) as total_income
                        FROM car_repair cr
                        JOIN faults f ON cr.fault_id = f.fault_id
                        LEFT JOIN spare_parts sp ON cr.car_id = sp.car_id AND cr.fault_id = sp.fault_id
                        WHERE cr.admission_date BETWEEN %s AND %s
                        GROUP BY TO_CHAR(cr.admission_date, 'YYYY-MM')
                        ORDER BY month
                    """
                
                cursor = self.conn.cursor()
                
                if report_type in [0, 2]:
                    cursor.execute(query, (
                        start_date.date().toString("yyyy-MM-dd"),
                        end_date.date().toString("yyyy-MM-dd")
                    ))
                else:
                    cursor.execute(query)
                
                data = cursor.fetchall()
                
                # Показываем результат
                result_dialog = QDialog(dialog)
                result_dialog.setWindowTitle("Результат отчета")
                result_dialog.resize(700, 500)
                
                result_layout = QVBoxLayout(result_dialog)
                
                table = QTableWidget()
                table.setRowCount(len(data))
                
                if data:
                    table.setColumnCount(len(data[0]))
                    
                    # Заголовки
                    cursor.description
                    headers = [desc[0] for desc in cursor.description]
                    table.setHorizontalHeaderLabels(headers)
                    
                    # Данные
                    for row_idx, row in enumerate(data):
                        for col_idx, value in enumerate(row):
                            table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                
                result_layout.addWidget(table)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(result_dialog.accept)
                result_layout.addWidget(close_btn)
                
                result_dialog.exec()
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка генерации отчета: {str(e)}")
        
        button_box.accepted.connect(generate_report)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.exec()
    
    def run(self):
        """Запуск приложения"""
        self.window.show()
        sys.exit(self.app.exec())

# Запуск приложения
if __name__ == "__main__":
    app = SimpleDBApp()
    app.run()