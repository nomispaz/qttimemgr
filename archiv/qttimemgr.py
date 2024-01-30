########################################################################
# naming convention
# l<name>: List
# v<name>: Variable
# i<name>: Input Field
# b<name>: button
# o<name>: output field
# d<name>: dictionary
########################################################################

import sys, os
from subprocess import run
from time import sleep
from datetime import date, datetime, timedelta
from math import floor, ceil
import sqlite3

from PyQt6.QtCore import QSize, Qt, QProcess, QByteArray
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
        QApplication,
        QPushButton,
        QMainWindow,
        QWidget,
        QPlainTextEdit,
        QInputDialog,
        QLineEdit,
        QDialogButtonBox,
        QCompleter,
        QComboBox,
        QButtonGroup,
        QRadioButton,
        QCheckBox,
        QLabel,
        QDateTimeEdit
)

class QtTimeMgrWindow(QMainWindow):

    #add new project to database
    def addProject(self):
        #insert new project into database
        vSqlQuery = ''' INSERT INTO projects(name)
                        VALUES(?) '''
        vSqlData = (self.iProject.text(),)
        sqlResult = insertDbData(self.sqlCon, vSqlQuery, vSqlData)

        #update projectlist
        vSqlResults = selectDbData(self.sqlCon, """SELECT * from projects order by name asc""", ())
        self.lProjects = []
        for results in vSqlResults:
            self.lProjects.append(results[1])

        #transfer new list to completer
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.cProject.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.iProject.setCompleter(self.cProject)

        #print success message
        self.printMessage("Project " + self.iProject.text() + " saved.")

    #start timer for project
    #create project if it doesn't exist
    def startTimer(self):
        #read entered project
        self.curProject = self.iProject.text()
        #if no project was entered, don't start tracking
        if self.curProject == "":
            self.printMessage("Please enter a project")
        else:
            #if project doesn't exist in database, create it
            vProjectsFromDB = selectDbData(self.sqlCon, """SELECT count(*) from projects where name = ?""", (self.curProject,))
            for result in vProjectsFromDB:
                projectcount = result[0]
            if projectcount == 0:
                self.addProject()

            self.startTime = datetime.now().strftime("%H:%M:%S")
            self.startTimestamp = datetime.timestamp(datetime.now())

            #print start message
            self.printMessage(
                str(self.startTime)
                + " : "
                + self.curProject
                + " , Tracking started "
                )

            #clear project field
            self.iProject.clear()

    #stop timer
    def endTimer(self):
        self.endTime = datetime.now().strftime("%H:%M:%S")
        self.endTimestamp = datetime.timestamp(datetime.now())
        #print end message
        self.printMessage(
            str(self.endTime)
            + " : "
            + self.curProject
            + " , Tracking ended. Duration: " + 
                #convert timestamps to hh:mm:ss
                str(
                    timedelta(seconds=
                        floor(self.endTimestamp-self.startTimestamp)
                    )
                )
            )
        
        #query on pk --> results in exactly one record
        vProjectsFromDB = selectDbData(self.sqlCon, """SELECT * from projects where name = ?""", (self.curProject,))
        
        #read project id from database
        for project in vProjectsFromDB:
            curProjectIdFromDb = project[0]

        #insert tracking result into database
        vSqlQuery = ''' INSERT INTO timetracking(project_id, date, calendarweek, month, year, starttimestamp, endtimestamp, created_on, last_edited_on)
                        VALUES(?,?,?,?,?,?,?,?,?) '''
        vSqlData = (curProjectIdFromDb, str(self.curDay), self.curWeek, self.curDay.month, self.curDay.year, floor(self.startTimestamp), floor(self.endTimestamp), str(self.curDay), str(self.curDay))
        sqlResult = insertDbData(self.sqlCon, vSqlQuery, vSqlData)

        #print result of insert statement
        self.printMessage(str(sqlResult))

    #save manually entered time
    def saveTimeSlot(self):
        self.curProject = self.iProject.text()
        self.curDay = self.iDatetimeStart.dateTime().toPyDateTime().date()
        #week
        self.curWeek = self.iDatetimeStart.dateTime().toPyDateTime().isocalendar()[1]
        #timestamp
        self.startTimestamp = datetime.timestamp(self.iDatetimeStart.dateTime().toPyDateTime())
        self.endTimestamp = datetime.timestamp(self.iDatetimeEnd.dateTime().toPyDateTime())

        #query on pk --> results in exactly one record
        vProjectsFromDB = selectDbData(self.sqlCon, """SELECT * from projects where name = ?""", (self.curProject,))
        
        #read project id from database
        for project in vProjectsFromDB:
            curProjectIdFromDb = project[0]

        #insert tracking result into database
        vSqlQuery = ''' INSERT INTO timetracking(project_id, date, calendarweek, month, year, starttimestamp, endtimestamp, created_on, last_edited_on)
                        VALUES(?,?,?,?,?,?,?,?,?) '''
        vSqlData = (curProjectIdFromDb, str(self.curDay), self.curWeek, self.curDay.month, self.curDay.year, floor(self.startTimestamp), floor(self.endTimestamp), str(self.curDay), str(self.curDay))
        sqlResult = insertDbData(self.sqlCon, vSqlQuery, vSqlData)

        #print result of insert statement
        self.printMessage(str(sqlResult))
        
    #toggle visibility of widgets for manual tracking if button is checked/unchecked
    def manualTracking(self):
        if self.bManualTracking.isChecked():
            self.iDatetimeStart.show()
            self.iDatetimeEnd.show()
            self.bSaveTimeslot.show()
        else:
            self.iDatetimeStart.hide()
            self.iDatetimeEnd.hide()
            self.bSaveTimeslot.hide()

    #print to Textbox
    def printMessage(self, s):
        self.oMainTextField.appendPlainText(s)

    #clear output window
    def clearOutput(self):
        self.oMainTextField.clear()

    #wrapper for transfer of select statement to database and print of result
    def getDataFromDb(self, vSqlQuery, vSqlData):
        vSelectFromDB = selectDbData(self.sqlCon, vSqlQuery, vSqlData)
        
        for result in vSelectFromDB:
            self.printMessage(str(result[0]) + "; " + result[1] + "; " + str(timedelta(seconds=result[2])))

    #wrapper for select statements of tracking results
    def getDataByMode(self, index):
        self.vGetDataMode = index
        match self.vGetDataMode:
            case 1:
                self.printMessage("Loading data for current day")
                
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Duration")
                    vSqlQuery = """SELECT t.date, p.name, t.endtimestamp-t.starttimestamp from timetracking t, projects p where t.date = ? and p.id=t.project_id"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, p.name, sum(t.endtimestamp-t.starttimestamp) from timetracking t, projects p where t.date = ? and p.id=t.project_id group by t.date, p.name"""
                vSqlData = (self.curDay,)
                self.getDataFromDb(vSqlQuery, vSqlData)
            case 2:
                self.printMessage("Loading data for yesterday")
                
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Duration")
                    vSqlQuery = """SELECT t.date, p.name, t.endtimestamp-t.starttimestamp from timetracking t, projects p where t.date = ? and p.id=t.project_id"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, p.name, sum(t.endtimestamp-t.starttimestamp) from timetracking t, projects p where t.date = ? and p.id=t.project_id group by t.date, p.name"""
                vSqlData = (self.curDay - timedelta(days=1),)
                self.getDataFromDb(vSqlQuery, vSqlData)
            case 3:
                self.printMessage("Loading data for current week")
              
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Duration")
                    vSqlQuery = """SELECT t.date, p.name, t.endtimestamp-t.starttimestamp from timetracking t, projects p where t.calendarweek = ? and t.year = ? and p.id=t.project_id"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, p.name, sum(t.endtimestamp-t.starttimestamp) from timetracking t, projects p where t.calendarweek = ? and t.year = ? and p.id=t.project_id group by t.date, p.name"""
                vSqlData = (self.curWeek, self.curDay.year)
                self.getDataFromDb(vSqlQuery, vSqlData)

            case 4:
                self.printMessage("Loading data for last week")
                self.printMessage("TODO")
            case 5:
                self.printMessage("Loading data for current month")
              
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Duration")
                    vSqlQuery = """SELECT t.date, p.name, t.endtimestamp-t.starttimestamp from timetracking t, projects p where t.month = ? and t.year = ? and p.id=t.project_id"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, p.name, sum(t.endtimestamp-t.starttimestamp) from timetracking t, projects p where t.month = ? and t.year = ? and p.id=t.project_id group by t.date, p.name"""
                vSqlData = (self.curDay.month, self.curDay.year)
                self.getDataFromDb(vSqlQuery, vSqlData)

            case 6:
                self.printMessage("Loading data for last month")
                self.printMessage("TODO")
            case 7:
                self.printMessage("Loading data for custom date")
                self.printMessage("TODO")

    #set whether tracking results should be summed
    def getSumOrSingle(self):
        self.vSumOrSingle = self.cSumOrSingle.isChecked()

    #cleanup database. Drop tables, then recreate tables
    def clearDatabase(self):
        result1 = drop_table(self.sqlCon, '''drop table projects;''')
        if result1 == "success":
            self.printMessage("Table project dropped successfully.")
        else:
            self.printMessage(result1)
        result2 = drop_table(self.sqlCon, '''drop table timetracking;''')
        if result2 == "success":
            self.printMessage("Table timetracking dropped successfully.")
        else:
            self.printMessage(result2)
        createDbModel(self.sqlCon)
        if result1 == "success":
            self.printMessage("Table project created successfully.")
        else:
            self.printMessage(result1)
        if result2 == "success":
            self.printMessage("Table timetracking created successfully.")
        else:
            self.printMessage(result2)
        

    def setupUI(self):
        #create widgets

        #Labels
        self.label1 = QLabel("QT Timetracker", self)
        self.label2 = QLabel("Results", self)
        self.label3 = QLabel("Misc", self)

        #project input field with completer
        self.iProject = QLineEdit(self)
        self.iProject.setPlaceholderText("Enter project")
        #completer
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.cProject.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.iProject.setCompleter(self.cProject)

        #create new project
        self.bNewProject = QPushButton("New", self)
        self.bNewProject.clicked.connect(self.addProject)

        #start timetracking
        self.bStart = QPushButton("Start",self)
        self.bStart.clicked.connect(self.startTimer)
        #end timetracking
        self.bEnd = QPushButton("End",self)
        self.bEnd.clicked.connect(self.endTimer)

        #manually create entry
        #button for manual entry
        self.bManualTracking = QPushButton("Manual", self)
        self.bManualTracking.setCheckable(True)
        self.bManualTracking.clicked.connect(self.manualTracking)

        #date and time field for manual tracking
        #hidden as standard
        self.iDatetimeStart = QDateTimeEdit(self)
        self.iDatetimeStart.setCalendarPopup(True)
        self.iDatetimeStart.setDateTime(datetime.today())
        self.iDatetimeStart.setDisplayFormat('dd.MM.yyyy hh:mm')
        self.iDatetimeStart.hide()

        #date and time field for manual tracking
        #hidden as standard
        self.iDatetimeEnd = QDateTimeEdit(self)
        self.iDatetimeEnd.setCalendarPopup(True)
        self.iDatetimeEnd.setDateTime(datetime.today())
        self.iDatetimeEnd.setDisplayFormat('dd.MM.yyyy hh:mm')
        self.iDatetimeEnd.hide()

        #button to save manual tracking
        self.bSaveTimeslot = QPushButton("Save time slot", self)
        self.bSaveTimeslot.clicked.connect(self.saveTimeSlot)
        self.bSaveTimeslot.hide()

        #clear output window
        self.bClear = QPushButton("Clear output",self)
        self.bClear.clicked.connect(self.clearOutput)

        #reset database
        self.bClearDb = QPushButton("Clear database",self)
        self.bClearDb.clicked.connect(self.clearDatabase)

        #output window
        self.oMainTextField = QPlainTextEdit(self)
        self.oMainTextField.setReadOnly(True)

        #dropdownlist of time intervals to load
        self.lGetData = QComboBox(self)
        self.lGetData.addItem("please select date")
        self.lGetData.addItem("current day")
        self.lGetData.addItem("last day")
        self.lGetData.addItem("current week")
        self.lGetData.addItem("last week")
        self.lGetData.addItem("current month")
        self.lGetData.addItem("last month")
        self.lGetData.addItem("custom date")
        self.lGetData.currentIndexChanged.connect(self.getDataByMode)

        #print sum per day and project or every single entry?
        self.cSumOrSingle = QCheckBox("Sum entries", self)
        self.cSumOrSingle.setChecked(True)
        self.cSumOrSingle.stateChanged.connect(self.getSumOrSingle)
  
        #resize widgets (x/y coordinates)
        #project input field
        self.label1.resize(200, 30)
        self.iProject.resize(300, 30)
        self.oMainTextField.resize(1000, 1000)
        self.lGetData.resize(250,30)
        self.cSumOrSingle.resize(250,30)
        self.bClear.resize(200,30)
        self.bClearDb.resize(200,30)
        self.iDatetimeStart.resize(250,30)
        self.iDatetimeEnd.resize(250,30)
        self.bSaveTimeslot.resize(250,30)

        #order Layout (x/y coordinates)
        #column 1
        self.label1.move(10, 10)
        self.iProject.move(10, 60)
        self.bNewProject.move(320, 60)
        self.bStart.move(10, 110)
        self.bEnd.move(120, 110)
        self.bManualTracking.move(230, 110)
        self.iDatetimeStart.move(340, 110)
        self.iDatetimeEnd.move(340, 150)
        self.bSaveTimeslot.move(600, 150)
        self.oMainTextField.move(10, 210)

        #column 2
        self.label2.move(510, 10)
        self.lGetData.move(510, 60)
        self.cSumOrSingle.move(770, 60)

        #column 3
        self.label3.move(1010, 10)
        self.bClear.move(1010,60)
        self.bClearDb.move(1010,110)
        

        

    def __init__(self, sqlVer, sqlCon):
        super().__init__()

        self.sqlCon = sqlCon

        #init variables
        self.lProjects = []
        self.curProject = ""
        self.startTime = 0
        self.startTimestamp = 0
        self.endTime = 0
        self.endTimestamp = 0
        self.vGetDataMode = 0
        self.vSumOrSingle = True

        self.curWeek = date.today().isocalendar()[1]
        self.curDay = date.today()

        #setup projects
        vSqlResults = selectDbData(sqlCon, """SELECT * from projects order by name asc""", ())
        for results in vSqlResults:
            self.lProjects.append(results[1])
       
        self.setWindowTitle("nomispaz Time Manager")
        self.setupUI()

        self.printMessage("Connected to sqlite database version " + str(sqlVer))
        


###############################################################################

def createDatabaseConnection(dbFile):
    DbConnection = None
    DbVersion = None
    try:
        DbConnection = sqlite3.connect(dbFile)
        DbVersion = sqlite3.version
    except sqlite3.Error as e:
        DbVersion = e
    return DbVersion, DbConnection

def create_table(conn, create_table_sql):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(create_table_sql)
        return "success"
    except sqlite3.Error as e:
        return e
    
def drop_table(conn, drop_table_sql):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(drop_table_sql)
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        return e


def createDbModel(conn):
    sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS projects (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL UNIQUE
                                    ); """

    sql_create_timetracking_table = """CREATE TABLE IF NOT EXISTS timetracking (
                                    id integer PRIMARY KEY,
                                    project_id integer,
                                    date text NOT NULL,
                                    calendarweek text NOT NULL,
                                    month text NOT NULL,
                                    year text NOT NULL,
                                    startTimestamp integer NOT NULL,
                                    endtimestamp,
                                    created_on,
                                    last_edited_on,
                                    FOREIGN KEY (project_id) REFERENCES projects (id)
                                );"""

    result1 = create_table(conn, sql_create_projects_table)
    result2 = create_table(conn, sql_create_timetracking_table)
    return result1, result2

def insertDbData(conn, sqlQuery, insertData):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(sqlQuery, insertData)
        conn.commit()
        return dbCursor.lastrowid
    except sqlite3.Error as e:
        print(e)

def selectDbData(conn, sqlQuery, whereData):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(sqlQuery, whereData)
        selectResults = dbCursor.fetchall()
        return selectResults
    except sqlite3.Error as e:
        return e


def main():

    vDbVersion = None
    vDbConnection = None
    #create Database-Connection to sqllite-DB
    #important: "~" for home doesn't work
    vDbVersion, vDbConnection = createDatabaseConnection(r'/home/simonheise/Documents/Coding/git_repos/qttimemgr/data/qttimemgr.db')
    if vDbConnection is not None:
        createDbModel(vDbConnection)

    # You need one (and only one) QApplication instance per application.
    # Pass in sys.argv to allow command line arguments for your app.
    # If you know you won't use command line arguments QApplication([]) works too.
    qttimemgrApp = QApplication(sys.argv)
    qttimemgrApp.setFont(QFont('Awesome', 20))

    # Create a Qt widget, which will be our window.
    qttimemgrWindow = QtTimeMgrWindow(vDbVersion, vDbConnection)
    # IMPORTANT!!!!! Windows are hidden by default.
    #qttimemgrWindow.setGeometry(500, 150, 500, 300)
    qttimemgrWindow.show()

    # Start the event loop.
    sys.exit(qttimemgrApp.exec())

    vDbConnection.close()

if __name__ == "__main__":
    main()
