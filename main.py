import sys
from datetime import datetime
import json
from PySide6.QtWidgets import (QApplication, QWidget, QCalendarWidget, QLabel,
                              QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit,
                              QMessageBox, QInputDialog,
                              QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import QDate, QDateTime, Qt, QTimer, QSize
from PySide6 import QtGui
from PySide6.QtGui import QTextCharFormat, QColor, QPixmap
from stylesheet import STYLESHEET
from os import path
import random


# Determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    APP_PATH = path.dirname(sys.executable)
elif __file__:
    APP_PATH = path.dirname(__file__)

TASKS_DATA_STORAGE=path.join(APP_PATH, "tasks.json")
CALENDAR_DATE_FORMAT="yyyyMMdd"

class TimePlanner(QWidget):
    # Keep the current time as class variable for reference
    current_day = str(datetime.now().day).rjust(2, '0')
    current_month = str(datetime.now().month).rjust(2, '0')
    current_year = str(datetime.now().year).rjust(2, '0')

    def __init__(self, width, height):
        super().__init__()
        self.icon_folder = path.join(APP_PATH, "media")
        self.setWindowTitle("TimePlanner")
        self.setWindowIcon(QtGui.QIcon(path.join(self.icon_folder, 'icon.ico')))

        self.setGeometry(width // 6, height // 6, width // 3, height // 3)
        self.current_task_status = {
            'index' : -1,
            'last_restart_time_secs' : 0,
            'last_total_time_secs': 0,
            'last_today_time_secs': 0
        }

        # Check if tasks storage file exists, if it does load the data from it
        file_exists = path.isfile(TASKS_DATA_STORAGE)
        try:
            if file_exists:
                with open(TASKS_DATA_STORAGE, "r") as file:
                    self.tasks = json.load(file)
            else:
                self.tasks = []
        except:
            QMessageBox.critical(self, "Error while loading tasks list", f"The tasks file: {TASKS_DATA_STORAGE} is broken. Application has to be closed")
            sys.exit(-1)

        print(f">>>>>>>>>>>self.tasks: {self.tasks}")
        self.init_ui()

    def init_ui(self):
        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(lambda: self.populate_tasks_info_table(self.tasks))
        self.calendar.selectionChanged.connect(self.label_date)
        self.calendar_displayed = False

        # Format for dates in calendar that have tasks
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor(255, 165, 0, 100))

        # Format for the current day
        cur_fmt = QTextCharFormat()
        cur_fmt.setBackground(QColor(0, 255, 90, 70))

        # Format to change back to if all tasks are deleted
        self.del_fmt = QTextCharFormat()
        self.del_fmt.setBackground(Qt.transparent)

        # Mark current day in calendar
        current = self.current_day + self.current_month + self.current_year
        self.calendar.setDateTextFormat(QDate.fromString(current, CALENDAR_DATE_FORMAT), cur_fmt)

        # Buttons
        add_button = QPushButton("Add Task")
        add_button.clicked.connect(self.add_task)
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_task)
        del_button = QPushButton("Delete")
        del_button.clicked.connect(self.remove_task)
        calendar_button = QPushButton("Calendar")
        pixmap = QPixmap(path.join(self.icon_folder, 'calendar.png'))
        size = QSize(16, 16)  # Adjust the size as needed
        pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QtGui.QIcon(pixmap)
        calendar_button.setIcon(icon)
        calendar_button.setIconSize(pixmap.size())
        calendar_button.clicked.connect(self.show_calendar)

        # Table widget
        self.tasks_info = QTableWidget()
        self.tasks_info.setColumnCount(3)
        self.tasks_info.setHorizontalHeaderLabels(["Name", "Today's Time Spent", "Total Time Spent"])
        # Set the columns to stretch equally
        for i in range(self.tasks_info.columnCount()):
            self.tasks_info.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.tasks_info.horizontalHeader().setStretchLastSection(True)
        # Connect the itemClicked signal to the slot for handling row selection
        self.tasks_info.itemClicked.connect(self.handle_task_item_clicked)
        self.populate_tasks_info_table(self.tasks)

        # Date label
        self.label = QLabel()
        label_font = QtGui.QFont("Gabriola", 18)
        self.label.setFont(label_font)
        self.label_date()

        # QTimer to update the time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_current_task_time)
        self.timer.start(1000)

        # Layouts
        label_h_layout = QHBoxLayout()
        label_h_layout.addStretch(1)
        label_h_layout.addWidget(self.label)
        label_h_layout.addStretch(1)

        buttons_h_layout = QHBoxLayout()
        buttons_h_layout.addWidget(add_button)
        buttons_h_layout.addWidget(edit_button)
        buttons_h_layout.addWidget(del_button)
        buttons_h_layout.addWidget(calendar_button)

        vbox = QVBoxLayout()
        vbox.addLayout(label_h_layout)
        vbox.addWidget(self.tasks_info)
        vbox.addLayout(buttons_h_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.calendar)
        self.calendar.setVisible(False)
        main_layout.addLayout(vbox)

        self.setLayout(main_layout)

    def populate_tasks_info_table(self, data, clear=True):
        ''' Update tasks_info table '''
        date = self.get_date()
        if clear:
            self.tasks_info.clearContents()
            self.tasks_info.setRowCount(len(data))

        for row, task in enumerate(data):
            name_item = QTableWidgetItem(task["name"])
            if date in task["today_time_spent"]:
                today_time_item = QTableWidgetItem(self.convert_secs_to_hh_mm_ss_format_string(task['today_time_spent'][date]))
            else:
                today_time_item = QTableWidgetItem("-")
            total_time_item = QTableWidgetItem(self.convert_secs_to_hh_mm_ss_format_string(task['total_time_spent']))
            self.tasks_info.setItem(row, 0, name_item)
            self.tasks_info.setItem(row, 1, today_time_item)
            self.tasks_info.setItem(row, 2, total_time_item)

    def handle_task_item_clicked(self, item):
        # Clear previous selection
        for row in range(self.tasks_info.rowCount()):
            for col in range(self.tasks_info.columnCount()):
                self.tasks_info.item(row, col).setSelected(False)
        # Highlight the entire row
        for col in range(self.tasks_info.columnCount()):
            self.tasks_info.item(item.row(), col).setSelected(True)
        self.current_task_status['index'] = item.row()
        # Start counting for newly selected task
        self.restart_current_task_time_counting()

    def add_task(self):
        date = self.get_date()
        title = "Add new task"
        name, ok = QInputDialog.getText(self, " ", title)

        if ok and name:
            # Is dict with a given nameexist
            for task in self.tasks:
                if task['name'] == name:
                    print(f"A task with the name '{name}' already exists.")
                    return False
            new_task = {
                'name' : name, 
                'created' : QDateTime.currentSecsSinceEpoch(),
                'today_time_spent' : {},
                'total_time_spent' : 0
            }
            self.tasks.append(new_task)

            item = QListWidgetItem(name)
            color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            item.setBackground(color)
            # Update all
            self.populate_tasks_info_table(self.tasks)
            self.calendar.setDateTextFormat(QDate.fromString(date, CALENDAR_DATE_FORMAT), self.fmt)
    
    def remove_task(self):
        # Get the currently selected row
        current_row = self.tasks_info.currentRow()
        if current_row >= 0:
            # Ask for confirmation before deleting
            reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to remove permanently {self.tasks[current_row]['name']} task?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Delete the row
                del self.tasks[current_row]
                self.tasks_info.removeRow(current_row)
                self.current_task_status['index'] = -1

    def edit_task(self):
        # Get the currently selected row
        current_row = self.tasks_info.currentRow()
        if current_row >= 0:
            item = self.tasks_info.item(current_row, 0)
            if item:
                title = "Edit task name"
                new_name, ok = QInputDialog.getText(self, " ", title,
                                                QLineEdit.Normal, item.text())
                if ok and new_name:
                    self.tasks[current_row]['name'] = new_name
                    self.tasks_info.item(current_row, 0).setText(new_name)

    def restart_current_task_time_counting(self):
        ''' Restart counting for a given task ''' 
        self.current_task_status['last_restart_time_secs'] = QDateTime.currentSecsSinceEpoch()
        self.current_task_status['last_total_time_secs'] = self.tasks[self.current_task_status['index']]['total_time_spent']
        date = self.get_date()
        if date not in self.tasks[self.current_task_status['index']]['today_time_spent']:
            self.tasks[self.current_task_status['index']]['today_time_spent'].update({date: 0})
        self.current_task_status['last_today_time_secs'] = self.tasks[self.current_task_status['index']]['today_time_spent'][date]
        self.update_current_task_time()

    def update_current_task_time(self):
        ''' Update time of currently selected task '''
        date = self.get_date()
        if self.current_task_status['index'] > -1:
            self.tasks[self.current_task_status['index']]['total_time_spent'] = QDateTime.currentSecsSinceEpoch() - self.current_task_status['last_restart_time_secs'] + self.current_task_status['last_total_time_secs']
            # Check if today stats exist for the task
            if date in self.tasks[self.current_task_status['index']]['today_time_spent']:
                self.tasks[self.current_task_status['index']]['today_time_spent'][date] = QDateTime.currentSecsSinceEpoch() - self.current_task_status['last_restart_time_secs'] + self.current_task_status['last_today_time_secs']
            else:
                self.tasks[self.current_task_status['index']]['today_time_spent'].update({date: 0})
            # Update UI
            self.populate_tasks_info_table(self.tasks, clear=False)

    def get_date(self):
        # Parse the selected date into usable string form
        select = self.calendar.selectedDate()
        date = str(select.year()) + '-' + str(select.month()).rjust(2, '0') + '-' + str(select.day()).rjust(2, '0')
        return date
    
    @staticmethod
    def convert_secs_to_hh_mm_ss_format_string(timestamp_secs: int):
        # Calculate hours, minutes, and seconds
        hours, remainder = divmod(timestamp_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        # Format the result as "hh:mm:ss"
        formatted_time = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
        return formatted_time

    def label_date(self):
        # Label to show the selected date
        select = self.calendar.selectedDate()
        day = str(select.day())
        year = str(select.year())
        week_day = select.toString("dddd")
        word_month = select.toString("MMMM")
        self.label.setText(week_day + ", " + word_month + " " + day + ", " + year)

    def show_calendar(self):
        # Display calendar widget
        if self.calendar_displayed:
            self.calendar_displayed = False
        else:
            self.calendar_displayed = True
        self.calendar.setVisible(self.calendar_displayed)
           
    def closeEvent(self, e):
        # Dump tasks data into json file when user closes app
        with open(TASKS_DATA_STORAGE, "w") as file:
            json.dump(self.tasks, file)
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    screen = app.primaryScreen()
    size = screen.size()
    window = TimePlanner(size.width(), size.height())
    window.show()
    sys.exit(app.exec())
