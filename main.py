import sys
from datetime import datetime
import json
from PySide6.QtWidgets import (QApplication, QWidget, QCalendarWidget, QLabel,
                              QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit,
                              QListWidget, QMessageBox, QInputDialog,
                              QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import QDate, QDateTime, Qt, QTimer, QTime, QSize
from PySide6 import QtGui
from PySide6.QtGui import QTextCharFormat, QColor, QPixmap
from stylesheet import STYLESHEET
from os import path
import random


TASKS_DATA_STORAGE=path.join(path.dirname(__file__), "tasks.json")

class TimePlanner(QWidget):
    # keep the current time as class variable for reference
    current_day = str(datetime.now().day).rjust(2, '0')
    current_month = str(datetime.now().month).rjust(2, '0')
    current_year = str(datetime.now().year).rjust(2, '0')

    def __init__(self, width, height):
        super().__init__()
        folder = path.dirname(__file__)
        self.icon_folder = path.join(folder, "icons")

        self.setWindowTitle("Planner")
        self.setWindowIcon(QtGui.QIcon(path.join(self.icon_folder, 'icon.png')))

        self.setGeometry(width // 6, height // 6, width // 3, height // 3)
        self.current_task = None

        # Check if tasks storage file exists, if it does load the data from it
        file_exists = path.isfile(TASKS_DATA_STORAGE)
        if file_exists:
            with open(TASKS_DATA_STORAGE, "r") as file:
                self.tasks = json.load(file)
        else:
            self.tasks = []

        print(f">>>>>>>>>>>self.tasks: {self.tasks}")
        
        self.init_ui()

    def init_ui(self):
        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        #self.calendar.selectionChanged.connect(self.populate_tasks_info_table(self.tasks)) #LU_TODO
        self.calendar.selectionChanged.connect(self.label_date)
        self.calendar.selectionChanged.connect(self.highlight_first_item)
        # don't allow going back to past months in calendar
        self.calendar.setMinimumDate(QDate(int(self.current_year), int(self.current_month), 1))

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
        self.calendar.setDateTextFormat(QDate.fromString(current, "ddMMyyyy"), cur_fmt)

        # Buttons
        add_button = QPushButton("Add Task")
        add_button.clicked.connect(self.add_task)
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_task)
        del_button = QPushButton("Delete")
        del_button.clicked.connect(self.edit_task)
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
        #self.tasks_info.setStyleSheet("QTableView::item {height: 40px;}")
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
        hbox1 = QHBoxLayout()
        hbox1.addStretch(1)
        hbox1.addWidget(self.label)
        hbox1.addStretch(1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(add_button)
        hbox2.addWidget(edit_button)
        hbox2.addWidget(del_button)
        hbox2.addWidget(calendar_button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.tasks_info)
        vbox.addLayout(hbox2)

        # hbox = QHBoxLayout()
        # hbox.addWidget(self.calendar, 55)
        # hbox.addLayout(vbox, 45)

        self.setLayout(vbox)
        #self.setWindowFlag(Qt.Tool)
        #self.setWindowFlags(Qt.WA_TranslucentBackground)#Qt.FramelessWindowHint)

    def populate_tasks_info_table(self, data):
        # Update tasks_info table
        date = self.get_date()
        self.tasks_info.clearContents()
        self.tasks_info.setRowCount(len(data))

        for row, task in enumerate(data):
            name_item = QTableWidgetItem(task["name"])
            total_time_item = QTableWidgetItem(task["total_time_spent"])
            if date in task["today_time_spent"]:
                today_time_item = QTableWidgetItem(task["today_time_spent"][date])
            else:
                today_time_item = QTableWidgetItem("-")
            self.tasks_info.setItem(row, 0, name_item)
            self.tasks_info.setItem(row, 1, total_time_item)
            self.tasks_info.setItem(row, 2, today_time_item)

    def handle_task_item_clicked(self, item):
        # Clear previous selection
        for row in range(self.tasks_info.rowCount()):
            for col in range(self.tasks_info.columnCount()):
                self.tasks_info.item(row, col).setSelected(False)
        # Highlight the entire row
        for col in range(self.tasks_info.columnCount()):
            self.tasks_info.item(item.row(), col).setSelected(True)
        self.current_task = item.row()

    def add_task(self):
        date = self.get_date()
        row = self.tasks_info.rowCount() + 1
        title = "Add task"
        name, ok = QInputDialog.getText(self, " ", title)

        if ok and name:
            # Is dict with a given nameexist
            for task in self.tasks:
                if task['name'] == name:
                    print(f"A task with the name '{name}' already exists.")
                    return False
            new_task = {
                'name' : name, 
                'created' : QDateTime.currentMSecsSinceEpoch(),
                'today_time_spent' : [],
                'total_time_spent' : 0
            }
            self.tasks.append(new_task)

            item = QListWidgetItem(name)
            color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            item.setBackground(color)

            # Update all
            self.populate_tasks_info_table(self.tasks)

            self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.fmt)

    def remove_task(self):
        #LU_TODO Delete the currently selected item
        date = self.get_date()
        row = self.tasks_info.currentRow()
        item = self.tasks_info.item(row)

        if not item:
            return
        reply = QMessageBox.question(self, " ", "Remove",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            item = self.tasks_info.takeItem(row)
            self.tasks[date].remove(item.text())
            if not self.tasks[date]:
                del(self.tasks[date])
                self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.del_fmt)
            del(item)

    def edit_task(self):
        # LU_TODO edit the currently selected item
        date = self.get_date()
        row = self.tasks_info.currentRow()
        item = self.tasks_info.item(row)

        if item:
            copy = item.text()
            title = "Edit task"
            string, ok = QInputDialog.getText(self, " ", title,
                                              QLineEdit.Normal, item.text())
            if ok and string:
                self.tasks[date].remove(copy)
                self.tasks[date].append(string)
                if string[0].isdigit() and string[0] not in ["0", "1", "2"]:
                    string = string.replace(string[0], "0" + string[0])
                item.setText(string)


    def update_current_task_time(self):
        current_time = QTime.currentTime()
        formatted_time = current_time.toString("hh:mm:ss")
        if self.current_task:
            self.tasks_info.item(self.current_task, 1).setText(formatted_time)
        #for row in range(self.tasks_info.rowCount()):
        #    self.tasks_info.item(row, 1).setText(formatted_time)

    def get_date(self):
        # Parse the selected date into usable string form
        select = self.calendar.selectedDate()
        date = str(select.year()) + '-' + str(select.month()).rjust(2, '0') + '-' + str(select.day()).rjust(2, '0')
        return date

    def label_date(self):
        # label to show the long name form of the selected date
        # format US style like "Thursday, February 20, 2020"
        select = self.calendar.selectedDate()
        weekday = select.dayOfWeek()
        month = select.month()
        day = str(select.day())
        year = str(select.year())
        week_day = select.addDays(weekday - 1).toString("dddd")
        word_month = select.toString("MMMM")
        self.label.setText(week_day + ", " + word_month + " " + day + ", " + year)

    def highlight_first_item(self):
        # highlight the first item immediately after switching selection
        if self.tasks_info.count() > 0:
            self.tasks_info.setCurrentRow(0)

    def show_calendar(self):
        pass

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
