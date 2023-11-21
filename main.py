import sys
from datetime import datetime
import json
from PySide6.QtWidgets import (QApplication, QWidget, QCalendarWidget, QLabel,
                              QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit,
                              QListWidget, QMessageBox, QInputDialog, QLCDNumber,
                              QListWidgetItem)
from PySide6.QtCore import QDate, QDateTime, Qt, QTimer, QTime, QSize
from PySide6 import QtGui
from PySide6.QtGui import QTextCharFormat, QColor, QPixmap
from stylesheet import STYLESHEET
from os import path
import random


TASKS_DATA_STORAGE=path.join(path.dirname(__file__), "tasks.json")

class TimePlanner(QWidget):
    # keep the current time as class variable for reference
    currentDay = str(datetime.now().day).rjust(2, '0')
    currentMonth = str(datetime.now().month).rjust(2, '0')
    currentYear = str(datetime.now().year).rjust(2, '0')

    def __init__(self, width, height):
        super().__init__()
        folder = path.dirname(__file__)
        self.icon_folder = path.join(folder, "icons")

        self.setWindowTitle("Planner")
        self.setWindowIcon(QtGui.QIcon(path.join(self.icon_folder, 'icon.png')))

        self.setGeometry(width // 4, height // 4, width // 2, height // 2)
        self.current_task = 0

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
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)

        # don't allow going back to past months in calendar
        self.calendar.setMinimumDate(QDate(int(self.currentYear), int(self.currentMonth), 1))

        # format for dates in calendar that have tasks
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor(255, 165, 0, 100))

        # format for the current day
        cur_fmt = QTextCharFormat()
        cur_fmt.setBackground(QColor(0, 255, 90, 70))

        # format to change back to if all tasks are deleted
        self.del_fmt = QTextCharFormat()
        self.del_fmt.setBackground(Qt.transparent)

        # # Show all the tasks
        # cur = QDate.currentDate()
        # for date in list(self.tasks.keys()):
        #     check_date = QDate.fromString(date, "yyyyMMdd")
        #     if cur.daysTo(check_date) <= 0 and cur != check_date:
        #         self.tasks.pop(date)
        #     else:
        #         self.calendar.setDateTextFormat(check_date, self.fmt)

        # Mark current day in calendar
        current = self.currentDay + self.currentMonth + self.currentYear
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

        self.calendar.selectionChanged.connect(self.show_tasks_list)
        self.calendar.selectionChanged.connect(self.label_date)
        self.calendar.selectionChanged.connect(self.highlight_first_item)

        self.tasks_list = QListWidget()
        self.tasks_list.setSortingEnabled(True)
        self.tasks_list.setStyleSheet("QListView::item {height: 40px;}")

        self.label = QLabel()
        label_font = QtGui.QFont("Gabriola", 18)
        self.label.setFont(label_font)
        self.label_date()
        self.show_tasks_list()

        # Set up a timer that automatically updates every second
        self.lcd = QLCDNumber()
        self.lcd.setSegmentStyle(QLCDNumber.Filled)
        self.lcd.setMinimumWidth(80)
        timer = QTimer(self)
        timer.timeout.connect(self.show_time)
        timer.start(1000)
        self.show_time()

        hbox1 = QHBoxLayout()
        hbox1.addStretch(1)
        hbox1.addWidget(self.label)
        hbox1.addStretch(1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(add_button)
        hbox2.addWidget(edit_button)
        hbox2.addWidget(del_button)
        hbox2.addWidget(calendar_button)

        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(self.lcd)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.tasks_list)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        # hbox = QHBoxLayout()
        # hbox.addWidget(self.calendar, 55)
        # hbox.addLayout(vbox, 45)

        self.setLayout(vbox)
        #self.setWindowFlag(Qt.Tool)
        #self.setWindowFlags(Qt.WA_TranslucentBackground)#Qt.FramelessWindowHint)

    def show_tasks_list(self):
        # Show Tasks
        date = self.get_date()
        self.tasks_list.clear()
        for task in self.tasks:
            self.tasks_list.addItem(task['name'])

    def add_task(self):
        date = self.get_date()
        row = self.tasks_list.currentRow()
        title = "Add task"
        name, ok = QInputDialog.getText(self, " ", title)

        if ok and name:
            # Is dict with a given nameexist
            for task in self.tasks:
                if task['name'] == name:
                    print(f"A task with the name '{name}' already exists.")
                    return False

            self.tasks.append({
                'name' : name, 
                'created' : QDateTime.currentMSecsSinceEpoch(),
                'total_time_spent' : 0,
                'time_spent_daily' : []
            })

            item = QListWidgetItem(name)
            color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            item.setBackground(color)
            self.tasks_list.addItem(item)
            self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.fmt)

    def remove_task(self):
        # delete the currently selected item
        date = self.get_date()
        row = self.tasks_list.currentRow()
        item = self.tasks_list.item(row)

        if not item:
            return
        reply = QMessageBox.question(self, " ", "Remove",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            item = self.tasks_list.takeItem(row)
            self.tasks[date].remove(item.text())
            if not self.tasks[date]:
                del(self.tasks[date])
                self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.del_fmt)
            del(item)

    def edit_task(self):
        # edit the currently selected item
        date = self.get_date()
        row = self.tasks_list.currentRow()
        item = self.tasks_list.item(row)

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
        if self.tasks_list.count() > 0:
            self.tasks_list.setCurrentRow(0)

    def show_time(self):
        # keep the current time updated
        time = QTime.currentTime()

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
