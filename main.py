import datetime
import os
import sqlite3
import sys
import threading

import PySide6
from PySide6.QtCore import QDateTime, Qt, QSize, QTimer
from PySide6.QtGui import QCursor, QIcon, QPalette, QBrush, QLinearGradient, QColor
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow,
    QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QDialog, QStackedWidget, QDateTimeEdit, QLineEdit,
    QMessageBox
)

dirname = os.path.dirname(PySide6.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

con = sqlite3.connect("taskManager.db", check_same_thread=False)
cur = con.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS tasks(title, text_content, time_limit)")
cur.execute(
    "CREATE TABLE IF NOT EXISTS finished_tasks(title, text_content, time_done)")


class mainApp(QMainWindow):
    def __init__(self, parent=None):
        super(mainApp, self).__init__(parent)

        self.setWindowIcon(QIcon("img/appIcon.png"))
        self.setWindowTitle("To-do list")
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.display_widget = displayTasksScreen(self)
        self.central_widget.addWidget(self.display_widget)
        self.central_widget.setStyleSheet(
            "background-color:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4262e3,stop:1 #F8CDDA)")

        self.finishedTasks_widget = finishedTasks(self)
        self.finishedTasks_widget.setStyleSheet("""
            QWidget{background-color:none}
            QLabel{font-size:16pt; margin:0 auto}
            QToolTip{background-color:none}
         """)
        self.central_widget.addWidget(self.finishedTasks_widget)
        self.display_widget.setStyleSheet("""
                QLabel{font-size: 17pt; margin: 0 auto; width:70px}
                QLineEdit{font-size:10pt; height:25px; padding-left:3px; background-color:none; outline:none; border-radius:7px; margin:0 auto; width:70px}
                QLineEdit:focus{border:1px solid #3232a8;}
                QDateTimeEdit{font-size:10pt; height:25px; padding-left:3px;text-align:center; background-color:none; border:none; border-radius:7px;}
                QDateTimeEdit:focus{border:1px solid #3232a8;}
                QWidget{background-color:none}
                QToolTip{background-color:none}
                """)

        self.central_widget.setCurrentWidget(self.display_widget)
        self.SwitchSize(0)

    def SwitchScreen(self, screen):
        if screen == 1:
            self.central_widget.setCurrentWidget(self.finishedTasks_widget)
            self.setWindowTitle("Finished Tasks")
            self.finishedTasks_widget.generateData()
            self.central_widget.setStyleSheet(
                "background-color:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #c8f2c2,stop:1 #6da23f)")
            self.SwitchSize(1)
        elif screen == 0:
            self.display_widget.updateData()
            self.central_widget.setCurrentWidget(self.display_widget)
            self.setWindowTitle("To-do list")
            self.central_widget.setStyleSheet(
                "background-color:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4262e3,stop:1 #F8CDDA)")
            self.SwitchSize(0)

    def SwitchSize(self, screen):
        if screen == 0:
            self.setFixedSize(1000, self.display_widget.calcHeight())
            if self.display_widget.calcHeight() < 200: self.setFixedSize(1000, 200)
        elif screen == 1:
            self.setFixedSize(800, self.finishedTasks_widget.calcHeight())
            if self.finishedTasks_widget.calcHeight() < 200: self.setFixedSize(800, 200)


class finishedTasks(QWidget):
    def __init__(self, parent=None):
        super(finishedTasks, self).__init__(parent)

        self.tasks = []

        self.layout = QGridLayout()

        self.generateData()

        self.timer = QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.generateData)
        self.timer.start()

    def generateData(self):
        self.getTasks()

        children = []
        for i in range(self.layout.count()):
            child = self.layout.itemAt(i).widget()
            if child:
                children.append(child)
        for child in children:
            if child:
                child.deleteLater()

        cancelBtn = QPushButton("")
        cancelBtn.setToolTip("Go back")
        cancelBtn.setFixedSize(50, 40)
        cancelBtn.setIconSize(QSize(30, 30))
        cancelBtn.setIcon(QIcon("img/cancel.png"))
        cancelBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancelBtn.setStyleSheet("border:none;")
        cancelBtn.clicked.connect(self.cancel)
        self.layout.addWidget(cancelBtn, 0, 0, Qt.AlignmentFlag.AlignCenter)

        headerMain = QLabel("FINISHED TASKS")
        headerMain.setStyleSheet("font-size:22pt; font-weight:600; text-align:center; text-decoration:underline;")
        self.layout.addWidget(headerMain, 0, 1, Qt.AlignmentFlag.AlignCenter)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 5)
        self.layout.setColumnStretch(2, 1)

        if len(self.tasks) == 0:
            self.layout.setColumnStretch(0,1)
            self.layout.setColumnStretch(1,8)
            self.layout.addWidget(QLabel("You haven't finished any tasks!"), 1, 1, Qt.AlignmentFlag.AlignCenter)

        for idx, task in enumerate(self.tasks):
            title = QLabel(task[0])
            self.layout.addWidget(title, idx + 1, 0, Qt.AlignmentFlag.AlignCenter)
            desc = QLabel(task[1])
            if len(task[1]) >= 43:
                desc.setText(task[1][:40] + "...")
            desc.setStyleSheet("width:400px")
            self.layout.addWidget(desc, idx + 1, 1, Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.generateTimeLabel(task[2][:19]), idx + 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.layout)

    def generateTimeLabel(self, timeString):
        dt = datetime.datetime.strptime(timeString, "%Y-%m-%d %H:%M:%S")
        delta = (datetime.datetime.now() - dt).total_seconds()
        if delta > 86400:
            return QLabel(str(round(delta / 86400)) + " days ago")
        elif delta > 3600:
            return QLabel(str(round(delta / 3600)) + " hours ago")
        elif delta > 60:
            return QLabel(str(round(delta / 60)) + " minutes ago")
        else:
            return QLabel("1 minute ago")

    def getTasks(self):
        self.tasks = cur.execute("SELECT * FROM finished_tasks").fetchall()

    def calcHeight(self):
        self.getTasks()
        return len(self.tasks) * 45 + 50

    def cancel(self):
        self.parent().parent().SwitchScreen(0)


class displayTasksScreen(QWidget):
    def __init__(self, parent=None):
        super(displayTasksScreen, self).__init__(parent)

        self.editedId = -1
        self.addingNewTask = False
        self.layout = QGridLayout()
        self.updateData()

        self.timer = QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.updateIfNotEditing)
        self.timer.start()

    def updateIfNotEditing(self):
        if self.editedId == -1 and self.addingNewTask is False: self.updateData()

    def updateData(self):
        print("UPDATING")
        children = []
        for i in range(self.layout.count()):
            child = self.layout.itemAt(i).widget()
            if child:
                children.append(child)
        for child in children:
            if child:
                child.deleteLater()
        if self.editedId == -1:
            headerMain = QLabel("TO DO LIST")
            headerMain.setStyleSheet("font-size:22pt; font-weight:600; text-align:center; text-decoration:underline;")
        else:
            headerMain = QLabel("EDITING...")
            headerMain.setStyleSheet("font-size:30pt; font-weight:600; text-align:center;color:blue")

        self.layout.addWidget(headerMain, 0, 1, Qt.AlignmentFlag.AlignCenter)
        lastindex = -1
        for i, task in enumerate(cur.execute(
                "SELECT title, text_content, time_limit, rowid FROM tasks ORDER BY time_limit")):
            if i > lastindex: lastindex = i
            taskDeadline = datetime.datetime.strptime(task[2][:19], "%Y-%m-%d %H:%M:%S")
            if task[3] == self.editedId:
                titleEntry = QLineEdit()
                descEntry = QLineEdit()
                timeEntry = QDateTimeEdit()

                titleEntry.setText(task[0])
                self.layout.addWidget(titleEntry, i + 1, 0, Qt.AlignmentFlag.AlignCenter)

                descEntry.setText(task[1])
                descEntry.setStyleSheet("width:350px")
                self.layout.addWidget(descEntry, i + 1, 1, Qt.AlignmentFlag.AlignCenter)

                timeEntry.setDateTime(QDateTime.fromString(task[2][:19], "yyyy-MM-dd hh:mm:ss"))
                timeEntry.setMinimumDateTime(QDateTime.currentDateTime().addSecs(-3600))
                self.layout.addWidget(timeEntry, i + 1, 2, Qt.AlignmentFlag.AlignCenter)

                cancelEditingBtn = QPushButton("")
                acceptEditBtn = QPushButton("")

                cancelEditingBtn.setToolTip("Cancel")
                cancelEditingBtn.setFixedSize(50, 40)
                cancelEditingBtn.setIconSize(QSize(30, 30))
                cancelEditingBtn.setIcon(QIcon("img/cancel.png"))
                cancelEditingBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                cancelEditingBtn.clicked.connect(self.cancelEditing)
                cancelEditingBtn.setStyleSheet("border:none;")
                self.layout.addWidget(cancelEditingBtn, i + 1, 4, Qt.AlignmentFlag.AlignCenter)

                acceptEditBtn.setToolTip("Accept")
                acceptEditBtn.setFixedSize(50, 40)
                acceptEditBtn.setIconSize(QSize(30, 30))
                acceptEditBtn.setIcon(QIcon("img/acceptEdit.png"))
                acceptEditBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                acceptEditBtn.clicked.connect(
                    lambda: self.acceptEditing(titleEntry, descEntry, timeEntry, self.editedId))
                acceptEditBtn.setStyleSheet("border:none;")
                self.layout.addWidget(acceptEditBtn, i + 1, 3, Qt.AlignmentFlag.AlignCenter)
            else:
                delta = (taskDeadline - datetime.datetime.now()).total_seconds()
                late = False
                if (delta < 0): late = True
                self.layout.addWidget(self.generateTimeLabel(delta), i + 1, 2, Qt.AlignmentFlag.AlignCenter)

                title = QLabel(task[0])
                if not late:
                    title.setStyleSheet("font-size:17pt; color: black")
                else:
                    title.setStyleSheet("font-size:17pt; color: #bd0000")
                self.layout.addWidget(title, i + 1, 0, Qt.AlignmentFlag.AlignCenter)

                descText = task[1]
                if len(descText) >= 43:
                    descText = descText[:40] + "..."
                desc = QLabel(descText)
                if not late:
                    desc.setStyleSheet("font-size:15pt; color: #303030")
                else:
                    desc.setStyleSheet("font-size:15pt; color: red")
                self.layout.addWidget(desc, i + 1, 1, Qt.AlignmentFlag.AlignCenter)

                finishTaskBtn = QPushButton('')
                editTaskBtn = QPushButton('')
                delTaskBtn = QPushButton('')

                for button in [finishTaskBtn, editTaskBtn, delTaskBtn]:
                    button.setStyleSheet("border:none;")
                    button.setFixedSize(50, 40)
                    button.setIconSize(QSize(40, 40))

                delTaskBtn.setToolTip("Delete")
                delTaskBtn.clicked.connect(lambda state=None, x=task[3]: self.deleteTask(x))
                delTaskBtn.setIcon(QIcon("img/delBtn.png"))
                delTaskBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                if not late:
                    finishTaskBtn.setToolTip("Mark as finished")
                    finishTaskBtn.clicked.connect(lambda state=None, x=task[3]: self.finishTask(x))
                    finishTaskBtn.setIcon(QIcon("img/doneBtn.png"))
                    finishTaskBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                    editTaskBtn.setToolTip("Edit")
                    editTaskBtn.clicked.connect(lambda state=None, x=task[3]: self.setEditedId(x))

                    editTaskBtn.setIcon(QIcon("img/editBtn.png"))
                    editTaskBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                else:
                    finishTaskBtn.setIcon(QIcon("img/doneBtnGrey.png"))
                    finishTaskBtn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

                    editTaskBtn.setIcon(QIcon("img/editBtnGrey.png"))
                    editTaskBtn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

                self.layout.addWidget(finishTaskBtn, i + 1, 3)
                self.layout.addWidget(editTaskBtn, i + 1, 4)
                self.layout.addWidget(delTaskBtn, i + 1, 5)

        if self.addingNewTask is False and self.editedId == -1:
            addTaskBtn = QPushButton("")
            addTaskBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            addTaskBtn.clicked.connect(self.switchAdding)
            addTaskBtn.setToolTip("Add new task")
            addTaskBtn.setFixedSize(45, 45)
            addTaskBtn.setIconSize(QSize(45, 45))
            addTaskBtn.setIcon(QIcon("img/addBtn.png"))
            addTaskBtn.setStyleSheet("border:none;")
            self.layout.addWidget(addTaskBtn, lastindex + 2, 4, Qt.AlignmentFlag.AlignCenter)

            completedTasksBtn = QPushButton("")

            completedTasksBtn.setToolTip("Completed tasks")
            completedTasksBtn.setFixedSize(45, 45)
            completedTasksBtn.setIconSize(QSize(45, 45))
            completedTasksBtn.setIcon(QIcon("img/completed.png"))
            completedTasksBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            completedTasksBtn.clicked.connect(self.switchScreenToFinishedTasks)
            completedTasksBtn.setStyleSheet("border:none;")
            self.layout.addWidget(completedTasksBtn, lastindex + 2, 5, Qt.AlignmentFlag.AlignCenter)

            if lastindex == -1:
                self.layout.addWidget(QLabel("No Tasks"), lastindex + 2, 1, Qt.AlignmentFlag.AlignCenter)
        elif self.addingNewTask and self.editedId == -1:
            labelNewTask = QLabel("NEW TASK:")
            labelNewTask.setStyleSheet("color:#ffb72c; font-weight:600; margin-top:25px")
            self.layout.addWidget(labelNewTask, lastindex + 2, 1, Qt.AlignmentFlag.AlignCenter)
            titleEntry = QLineEdit()
            descEntry = QLineEdit()
            timeEntry = QDateTimeEdit()
            titleEntry.setPlaceholderText("title")
            self.layout.addWidget(titleEntry, lastindex + 3, 0, Qt.AlignmentFlag.AlignCenter)
            descEntry.setPlaceholderText("description")
            descEntry.setStyleSheet("width:350px")
            self.layout.addWidget(descEntry, lastindex + 3, 1, Qt.AlignmentFlag.AlignCenter)
            timeEntry.setDateTime(QDateTime.currentDateTime().addDays(2))
            timeEntry.setMinimumDateTime(QDateTime.currentDateTime().addSecs(-3600))
            self.layout.addWidget(timeEntry, lastindex + 3, 2, Qt.AlignmentFlag.AlignCenter)

            cancelAddingBtn = QPushButton("")
            acceptAddingBtn = QPushButton("")

            cancelAddingBtn.setToolTip("Cancel")
            cancelAddingBtn.setFixedSize(50, 40)
            cancelAddingBtn.setIconSize(QSize(30, 30))
            cancelAddingBtn.setIcon(QIcon("img/cancel.png"))
            cancelAddingBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cancelAddingBtn.clicked.connect(self.switchAdding)
            cancelAddingBtn.setStyleSheet("border:none;")
            self.layout.addWidget(cancelAddingBtn, lastindex + 3, 4, Qt.AlignmentFlag.AlignCenter)

            acceptAddingBtn.setToolTip("Accept")
            acceptAddingBtn.setFixedSize(50, 40)
            acceptAddingBtn.setIconSize(QSize(30, 30))
            acceptAddingBtn.setIcon(QIcon("img/acceptEdit.png"))
            acceptAddingBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            acceptAddingBtn.clicked.connect(
                lambda: self.addTask(titleEntry, descEntry, timeEntry))
            acceptAddingBtn.setStyleSheet("border:none;")
            self.layout.addWidget(acceptAddingBtn, lastindex + 3, 3, Qt.AlignmentFlag.AlignCenter)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 4)
        self.layout.setColumnStretch(2, 2)
        self.layout.setColumnStretch(3, 1)
        self.layout.setColumnStretch(4, 1)
        self.layout.setColumnStretch(5, 1)
        if lastindex == -1:
            self.layout.setColumnStretch(0, 1)
            self.layout.setColumnStretch(1, 9)
            self.layout.setColumnStretch(2, 0)
            self.layout.setColumnStretch(3, 0)
            self.layout.setColumnStretch(4, 1)
            self.layout.setColumnStretch(5, 1)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.update()

    def addTask(self, title, desc, timedata):
        if len(title.text()) < 1:
            QMessageBox.critical(self, "Error", "Title can not be empty!")
        elif len(desc.text()) < 1:
            QMessageBox.critical(self, "Error", "Description can not be empty!")
        elif timedata.dateTime().secsTo(QDateTime.currentDateTime()) > 0:
            QMessageBox.critical(self, "Error", "Incorrect deadline!")
        else:
            cur.execute(f"""
                INSERT INTO tasks VALUES ('{title.text()}', '{desc.text()}', '{timedata.dateTime().toPython()}')
            """)
            con.commit()
            self.parent().parent().SwitchSize(0)
            self.switchAdding()

    def switchAdding(self):
        self.addingNewTask = not self.addingNewTask
        if self.addingNewTask and self.editedId != -1: self.cancelEditing()
        self.updateData()

    def acceptEditing(self, titleEntry, descEntry, timeEntry, rowid):
        if len(titleEntry.text()) < 1:
            QMessageBox.critical(self, "Error", "Title can not be empty!")
        elif len(descEntry.text()) < 1:
            QMessageBox.critical(self, "Error", "Description can not be empty!")
        elif timeEntry.dateTime().secsTo(QDateTime.currentDateTime()) > 0:
            QMessageBox.critical(self, "Error", "Incorrect deadline!")
        else:
            cur.execute(f"""
                UPDATE tasks SET title='{titleEntry.text()}', text_content='{descEntry.text()}', time_limit='{timeEntry.dateTime().toPython()}' WHERE rowid={rowid}
            """)
            con.commit()
            self.cancelEditing()

    def cancelEditing(self):
        self.editedId = -1
        self.updateData()

    def setEditedId(self, rowid):
        if self.addingNewTask: self.switchAdding()
        self.editedId = rowid
        self.updateData()

    def finishTask(self, rowid):
        theTask = cur.execute("SELECT * FROM tasks WHERE rowid=" + str(rowid)).fetchone()
        cur.execute("DELETE FROM tasks WHERE rowid=" + str(rowid))
        cur.execute(
            f"INSERT INTO finished_tasks VALUES ('{theTask[0]}','{theTask[1]}','{datetime.datetime.now()}')")
        con.commit()
        self.updateData()

    def switchScreenToFinishedTasks(self):
        self.parent().parent().SwitchScreen(1)

    def deleteTask(self, rowid):
        cur.execute("DELETE FROM tasks WHERE rowid=" + str(rowid))
        con.commit()
        self.parent().parent().SwitchSize(0)
        self.updateData()

    @staticmethod
    def generateTimeLabel(delta):
        if delta > 86400:  # more than 24 hours
            style = "color: #292929"
            labelText = str(round(delta / 86400)) + " days left"
            if round(delta / 86400) < 2:
                labelText = "1 day left"
        elif delta > 3600:  # more than 1 hour
            style = ""
            labelText = str(round(delta / 3600)) + " hours left"
            if round(delta / 3600) < 2:
                labelText = "1 hour left"
        elif delta > 0:
            style = "color:#bd7800; font-weight:600"
            labelText = str(round(delta / 60)) + " minutes left"
            if round(delta / 60) < 2:
                labelText = "1 minute left"
        elif delta > -3600:
            style = "color:#ff1f1f; font-weight:600;"
            labelText = str(abs(round(delta / 60))) + " minutes late!"
            if abs(round(delta / 60)) < 2:
                labelText = "1 minute late!"
        elif delta > -86400:
            style = "color:#ff1f1f; font-weight:600"
            labelText = str(abs(round(delta / 3600))) + " hours late!"
            if abs(round(delta / 3600)) < 2:
                labelText = "1 hour late!"
                labelText = "1 hour late!"
        else:
            style = "color:#ff1f1f; font-weight:600"
            labelText = str(abs(round(delta / 86400))) + " days late!"
            if abs(round(delta / 86400)) < 2:
                labelText = "1 day late!"
        timeLeft = QLabel(labelText)
        timeLeft.setStyleSheet("font-size:13pt; " + style)
        return timeLeft

    def calcHeight(self):
        return len(cur.execute("SELECT * FROM tasks").fetchall()) * 45 + 180


app = QApplication(sys.argv)

window = mainApp()
window.show()

app.exec()
con.close()
