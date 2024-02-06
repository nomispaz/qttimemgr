'''
    Copyright (C) 2024  Simon Heise

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

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
from time import sleep, mktime
from datetime import date, datetime, timedelta
from math import floor, ceil
import sqlite3
from PyQt6 import uic

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
        QDateTimeEdit,
        QDialog,
        QAbstractItemView,
        QTableWidgetItem,
        QTableWidget
)

class QtListPopupDialog(QDialog):
    def getEntryList(self):
        return self.tShowTrackingEntries.selectedItems()

    def deleteEntry(self):
        lListofEntries = QTableWidgetItem()
        lListofEntries = self.getEntryList()

        firstItemIndex = lListofEntries[0].row()
        lastItemIndex = lListofEntries[len(lListofEntries) - 1].row()
        
        # create one sql-query for deletion of all selected items
        sqlQuery = "delete from timetracking where id in ( "

        #
        #lListofEntries contains list with all columns of all selected rows
        #-->delete entries where index%NumColumns=0
        for numEntry in range(0,len(lListofEntries) - 1):
            entrySplit = str(lListofEntries[numEntry].text())
            if numEntry%self.numColumns == 0:
                sqlQuery = sqlQuery + entrySplit + ","
        #cut last "," and finish query-string
        sqlQuery = sqlQuery[:-1] + " )"

        #Delete selection from database
        deletionResult = deleteDbData(self.sqlCon, sqlQuery, ())
        if deletionResult == 0:
            #items where deleted --> update table
            for numEntry in reversed(range(0,len(lListofEntries) - 1)):
                try:
                    self.tShowTrackingEntries.removeRow(lListofEntries[numEntry].row())
                except:
                    None

    def commitEntry(self):
        #write all changes into the database.
        #modus FIFO so that if an entry was changed multiple times, the last change will be committed last
        for entry in self.lChangedItems:
            #date, starttime, endtime,
            #compute starttimestamp, endtimestamp 
            starttimestamp = floor(mktime(datetime.strptime(entry[2].text() + " " + entry[3].text(), "%Y-%m-%d %H:%M:%S").timetuple()))
            endtimestamp = ceil(mktime(datetime.strptime(entry[2].text() + " " + entry[4].text(), "%Y-%m-%d %H:%M:%S").timetuple()))

            sqlQuery = ''' UPDATE timetracking 
                            SET date = ?, starttime = ?, starttimestamp = ?, endtime = ?, endtimestamp = ?
                            where id = ? '''
            sqlValues = (entry[2].text(), entry[3].text(), starttimestamp, entry[4].text(), endtimestamp, entry[0].text())
            sqlerr = updateDbData(self.sqlCon, sqlQuery, sqlValues)
    
    def changedItem(self):
        #save all changes in list
        self.lChangedItems.append(self.tShowTrackingEntries.selectedItems())
        for entry in self.lChangedItems:
            print(len(entry))
        
    def setupUIfunctions(self):

        #button to delete entries
        self.bDeleteEntry.clicked.connect(self.deleteEntry)

        #button to commit entry changes
        self.bEditEntry.clicked.connect(self.commitEntry)

        #button to close widget
        self.bCloseListPopup.clicked.connect(self.close)

        #enable multiselect in list
        self.tShowTrackingEntries.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tShowTrackingEntries.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        #fill list with tracking entries
        vSqlResults = selectDbData(self.sqlCon, """SELECT * from timetracking order by date, starttime asc""", ())
        self.lTrackingEntries = []
        self.numColumns = 5
        #dynamially set up table with columns and rows (number of columns equals to number of attributes in timetracking table)
        try:
            self.tShowTrackingEntries.setColumnCount(len(vSqlResults[0]))
        except:
            self.tShowTrackingEntries.setColumnCount(1)
        columnHeaders = (("id", "project_id", "project", "date", "calendarweek", "month", "year", "starttimestamp", "starttime", "endtimestamp", "endtime", "created_on", "last_edited_on"))
        self.tShowTrackingEntries.setHorizontalHeaderLabels(columnHeaders)
        self.tShowTrackingEntries.hideColumn(1)
        self.tShowTrackingEntries.hideColumn(4)
        self.tShowTrackingEntries.hideColumn(5)
        self.tShowTrackingEntries.hideColumn(6)
        self.tShowTrackingEntries.hideColumn(7)
        self.tShowTrackingEntries.hideColumn(9)
        self.tShowTrackingEntries.hideColumn(11)
        self.tShowTrackingEntries.hideColumn(12)
        
        
        #write sql results into list
        for results in vSqlResults:
            self.lTrackingEntries.append(results)

        #add rows to the table according to the number of tracking results
        self.tShowTrackingEntries.setRowCount(len(self.lTrackingEntries))
        
        #fill table with entries
        curRow = 0
        for trackingEntry in self.lTrackingEntries:
            for column in range(0,len(trackingEntry)):
                qtTableItem = QTableWidgetItem(str(trackingEntry[column]))
                if column == 0 or column == 2:
                    #show tracking id and project but don't allow to change
                    qtTableItem.setFlags(qtTableItem.flags() & ~Qt.ItemFlag.ItemIsEditable )
                self.tShowTrackingEntries.setItem(curRow, column, qtTableItem)
            curRow += 1

        #activate itemChanged signal for tShowTrackingEntries
        self.tShowTrackingEntries.itemChanged.connect(self.changedItem)

    def __init__(self, sqlCon, parent = None):

        #init variables
        self.lTrackingEntries = []
        self.sqlCon = sqlCon
        self.lChangedItems = []

        super(QtListPopupDialog, self).__init__(parent)
        self.absolute_path = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.absolute_path, "config/ui/QtListPopupDialog.ui"),self)

        self.setupUIfunctions()
        

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

        #check if a tracking is currently running
        if self.vTrackingIsRunning == True:
            #end it before starting a new tracking
            self.endTimer()

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

            #set variable to store if a tracking is currently running
            self.vTrackingIsRunning = True

            #clear project field
            self.iProject.clear()

    #stop timer
    def endTimer(self):
        if not self.curProject == "":
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
                curProjectNameFromDb = project[1]

            #insert tracking result into database
            vSqlQuery = ''' INSERT INTO timetracking(project_id, project_name, date, calendarweek, month, year, starttimestamp, starttime, endtimestamp, endtime, created_on, last_edited_on)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
            vSqlData = (curProjectIdFromDb, curProjectNameFromDb, str(self.curDay), self.curWeek, self.curDay.month, self.curDay.year, floor(self.startTimestamp), str(self.startTime), floor(self.endTimestamp), str(self.endTime), str(self.curDay), str(self.curDay))
            sqlResult = insertDbData(self.sqlCon, vSqlQuery, vSqlData)

            #set variable to store if a tracking is currently running
            self.vTrackingIsRunning = False

    #save manually entered time
    def saveTimeSlot(self):
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

            self.curDay = self.iDatetimeStart.dateTime().toPyDateTime().date()
            #week
            self.curWeek = self.iDatetimeStart.dateTime().toPyDateTime().isocalendar()[1]
            #start and end time
            self.startTime = self.iDatetimeStart.dateTime().toPyDateTime().time().strftime("%H:%M:%S")
            self.endTime = self.iDatetimeEnd.dateTime().toPyDateTime().time().strftime("%H:%M:%S")
            #timestamp
            self.startTimestamp = datetime.timestamp(self.iDatetimeStart.dateTime().toPyDateTime())
            self.endTimestamp = datetime.timestamp(self.iDatetimeEnd.dateTime().toPyDateTime())

            #query on pk --> results in exactly one record
            vProjectsFromDB = selectDbData(self.sqlCon, """SELECT * from projects where name = ?""", (self.curProject,))

            #read project id from database
            for project in vProjectsFromDB:
                curProjectIdFromDb = project[0]
                curProjectNameFromDb = project[1]

            #insert tracking result into database
            vSqlQuery = ''' INSERT INTO timetracking(project_id, project_name, date, calendarweek, month, year, starttimestamp, starttime, endtimestamp, endtime, created_on, last_edited_on)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
            vSqlData = (curProjectIdFromDb, curProjectNameFromDb, str(self.curDay), self.curWeek, self.curDay.month, self.curDay.year, floor(self.startTimestamp), str(self.startTime), floor(self.endTimestamp), str(self.endTime), str(self.curDay), str(self.curDay))
            sqlResult = insertDbData(self.sqlCon, vSqlQuery, vSqlData)

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
        
        vSumOfTimes = 0

        for result in vSelectFromDB:
            if self.vSumOrSingle == False: 
                self.printMessage(str(result[0]) + "; " + result[1] + "; " + result[3] + "; " + result[4] + "; " + str(timedelta(seconds=result[2])))
            else:
                self.printMessage(str(result[0]) + "; " + result[1] + "; " + str(timedelta(seconds=result[2])))
            
            vSumOfTimes += result[2]

        self.printMessage("------------------")
        self.printMessage("Sum: " + str(timedelta(seconds=vSumOfTimes)))

    #wrapper for select statements of tracking results
    def getDataByMode(self, index):
        self.vGetDataMode = index
        self.curDay = date.today()
        match self.vGetDataMode:
            case 1:
                self.printMessage("Loading data for current day")
                
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Starttime; Endtime Duration")
                    vSqlQuery = """SELECT t.date, t.project_name, t.endtimestamp-t.starttimestamp, t.starttime, t.endtime from timetracking t where t.date = ?"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, t.project_name, sum(t.endtimestamp-t.starttimestamp) from timetracking t where t.date = ?group by t.date, t.project_name"""
                vSqlData = (self.curDay,)
                self.getDataFromDb(vSqlQuery, vSqlData)
            case 2:
                self.printMessage("Loading data for yesterday")
                
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Starttime; Endtime Duration")
                    vSqlQuery = """SELECT t.date, t.project_name, t.endtimestamp-t.starttimestamp, t.starttime, t.endtime from timetracking t where t.date = ?"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, t.project_name, sum(t.endtimestamp-t.starttimestamp) from timetracking t where t.date = ? group by t.date, t.project_name"""
                vSqlData = (self.curDay - timedelta(days=1),)
                self.getDataFromDb(vSqlQuery, vSqlData)
            case 3:
                self.printMessage("Loading data for current week")
              
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Starttime; Endtime Duration")
                    vSqlQuery = """SELECT t.date, t.project_name, t.endtimestamp-t.starttimestamp, t.starttime, t.endtime from timetracking t where t.calendarweek = ? and t.year = ?"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, t.project_name, sum(t.endtimestamp-t.starttimestamp) from timetracking t where t.calendarweek = ? and t.year = ? group by t.date, t.project_name"""
                vSqlData = (self.curWeek, self.curDay.year)
                self.getDataFromDb(vSqlQuery, vSqlData)

            case 4:
                self.printMessage("Loading data for last week")
                self.printMessage("TODO")
            case 5:
                self.printMessage("Loading data for current month")
              
                if self.vSumOrSingle == False:
                    self.printMessage("Date; Project; Starttime; Endtime Duration")
                    vSqlQuery = """SELECT t.date, t.project_name, t.endtimestamp-t.starttimestamp, t.starttime, t.endtime from timetracking t where t.month = ? and t.year = ?"""
                else:
                    self.printMessage("Date; Project; Duration (sum)")
                    vSqlQuery = """SELECT t.date, t.project_name, sum(t.endtimestamp-t.starttimestamp) from timetracking t where t.month = ? and t.year = ? group by t.date, t.project_name"""
                vSqlData = (self.curDay.month, self.curDay.year)
                self.getDataFromDb(vSqlQuery, vSqlData)

            case 6:
                self.printMessage("Loading data for last month")
                self.printMessage("TODO")
            case 7:
                self.printMessage("Loading data for custom date")
                self.printMessage("TODO")
        self.lGetData.setCurrentIndex(0)

    #set whether tracking results should be summed
    def getSumOrSingle(self):
        self.vSumOrSingle = self.cSumOrSingle.isChecked()

    #cleanup database. Drop tables, then recreate tables
    def clearDatabase(self):

        self.sqlFile = os.path.join(self.absolute_path, "config/dbmodel/dropAllTables.sql")
        sqlerr, sqlQuery = execute_sqlfile(self.sqlCon, self.sqlFile)
        if sqlerr != 0:
            self.printMessage("SQL-Command " + sqlQuery + " failed with error: " + str(sqlerr))
        else:
            self.printMessage("SQL-skript " + self.sqlFile + " ran successful.")

        self.createDbModel()
        
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
    
    def deleteProject(self):
        vDeleteProject, okPressed = self.iDeleteProject = QInputDialog.getItem(self, "Enter Project", "Enter Project", self.lProjects, 0, False)
        if okPressed == 1:
            #query on pk --> results in exactly one record
            vProjectsFromDB = selectDbData(self.sqlCon, """SELECT * from projects where name = ?""", (vDeleteProject,))
            #read project id from database
            for project in vProjectsFromDB:
                curProjectIdFromDb = project[0]
            #delete project
            deleteDbData(self.sqlCon, """DELETE from projects where id = ?""", (curProjectIdFromDb,))
            
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

    def editDeleteTrackingEntry(self):
        # Create a Qt widget, which will be our window.
        self.qtlistpopupdialog = QtListPopupDialog(self.sqlCon)
        # IMPORTANT!!!!! Windows are hidden by default.
        #qttimemgrWindow.setGeometry(500, 150, 500, 300)
        self.qtlistpopupdialog.show()
        
    def updateModel(self, curDbVersion):
        #the datamodel exists at this moment
        for sqlFile in os.listdir(os.path.join(self.absolute_path, "config/dbmodel/")):
            #run all files if the databaseversion is smaller than the filename
            if sqlFile != "createModel.sql" and sqlFile != "dropAllTables.sql" and int(sqlFile.split(".")[0])>int(curDbVersion):
                self.sqlFile = os.path.join(self.absolute_path, "config/dbmodel/"+sqlFile)
                sqlerr, sqlQuery = execute_sqlfile(self.sqlCon, self.sqlFile)
                if sqlerr != 0:
                    self.printMessage("SQL-Command " + sqlQuery + " failed with error: " + str(sqlerr))
                else:
                    self.printMessage("SQL-skript " + self.sqlFile + " ran successful.")

    def createDbModel(self):
        #check the modelversion of the database
        vSqlResults = selectDbData(self.sqlCon, """SELECT max(modelversion) from databasemodel""", ())
        
        if str(vSqlResults) == "no such table: databasemodel":
            #initiate databasemodel
            self.sqlFile = os.path.join(self.absolute_path, "config/dbmodel/createModel.sql")
            sqlerr, sqlQuery = execute_sqlfile(self.sqlCon, self.sqlFile)
            if sqlerr != 0:
                self.printMessage("SQL-Command " + sqlQuery + " failed with error: " + str(sqlerr))
            else:
                self.printMessage("SQL-skript " + self.sqlFile + " ran successful.")
            vSqlResults = selectDbData(self.sqlCon, """SELECT max(modelversion) from databasemodel""", ())
        
        self.updateModel(str(vSqlResults[0][0]))
        

    def setupUIfunctions(self):
        
        #completer for project input field
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.cProject.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.iProject.setCompleter(self.cProject)

        #create new project
        self.bNewProject.clicked.connect(self.addProject)

        #start timetracking
        self.bStart.clicked.connect(self.startTimer)
        #end timetracking
        self.bEnd.clicked.connect(self.endTimer)

        #manually create entry
        #button for manual entry
        self.bManualTracking.clicked.connect(self.manualTracking)

        #date and time field for manual tracking
        #hidden as standard
        self.iDatetimeStart.setDateTime(datetime.today())
        self.iDatetimeStart.hide()

        #date and time field for manual tracking
        #hidden as standard
        self.iDatetimeEnd.setDateTime(datetime.today())
        self.iDatetimeEnd.hide()

        #button to save manual tracking
        self.bSaveTimeslot.clicked.connect(self.saveTimeSlot)
        self.bSaveTimeslot.hide()

        #clear output window
        self.bClear.triggered.connect(self.clearOutput)

        #reset database
        self.bClearDb.triggered.connect(self.clearDatabase)

        #dropdownlist of time intervals to load
        self.lGetData.currentIndexChanged.connect(self.getDataByMode)

        #print sum per day and project or every single entry?
        self.cSumOrSingle.stateChanged.connect(self.getSumOrSingle)

        #delete project from database
        self.bDeleteProject.triggered.connect(self.deleteProject)

        #delete single timetracking entry
        self.bEditDeleteTrackingEntry.triggered.connect(self.editDeleteTrackingEntry)
  

    def __init__(self, sqlVer, sqlCon):

        #init variables
        self.lProjects = []
        self.curProject = ""
        self.startTime = 0
        self.startTimestamp = 0
        self.endTime = 0
        self.endTimestamp = 0
        self.vGetDataMode = 0
        self.vSumOrSingle = True
        self.vTrackingIsRunning = False
        self.curWeek = date.today().isocalendar()[1]
        self.curDay = date.today()

        super(QtTimeMgrWindow, self).__init__()
        self.absolute_path = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.absolute_path, "config/ui/QtTimeMgrWindow.ui"),self)
        self.setupUIfunctions()

        # is a connection to the database possible, if yes, continue
        if sqlCon is not None:

            self.sqlCon = sqlCon
            self.createDbModel()

            #setup projects and feed to completer
            vSqlResults = selectDbData(sqlCon, """SELECT * from projects order by name asc""", ())
            for results in vSqlResults:
                self.lProjects.append(results[1])
            
            #transfer new list to completer
            self.cProject = QCompleter(self.lProjects,self)
            self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.cProject.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
            self.iProject.setCompleter(self.cProject)

            self.printMessage("Connected to sqlite database version " + str(sqlVer))
        
        else:
            self.printMessage("Not connected to sqlite database. Cannot continue")



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

def drop_table(conn, drop_table_sql):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(drop_table_sql)
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        return e

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

def updateDbData(conn, sqlQuery, sqlData):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(sqlQuery, sqlData)
        conn.commit()
        return 0
    except sqlite3.Error as e:
        return e

def deleteDbData(conn, sqlQuery, whereData):
    try:
        dbCursor = conn.cursor()
        dbCursor.execute(sqlQuery, whereData)
        conn.commit()
        return 0
    except sqlite3.Error as e:
        return e

def execute_sqlfile(conn, filename):
    try:
        dbCursor = conn.cursor()
        #read files into array aSqlFile
        filehandler = open(filename, 'r')
        aSqlFile = filehandler.read()
        aSqlFileSplit = aSqlFile.split("##")
        filehandler.close()
        for sqlQuery in aSqlFileSplit:
            dbCursor.execute(sqlQuery)
        conn.commit()
    except sqlite3.OperationalError as e:
        return e, sqlQuery
    return 0, 0

def main():

    vDbVersion = None
    vDbConnection = None
    #create Database-Connection to sqllite-DB
    #important: "~" for home doesn't work
    absolute_path = os.path.dirname(__file__)
    relative_path = "data"
    full_path = os.path.join(absolute_path, relative_path)
    vDbVersion, vDbConnection = createDatabaseConnection(full_path+'/qttimemgr.db')
    
    # You need one (and only one) QApplication instance per application.
    # Pass in sys.argv to allow command line arguments for your app.
    # If you know you won't use command line arguments QApplication([]) works too.
    qttimemgrApp = QApplication(sys.argv)
    qttimemgrApp.setFont(QFont('Awesome', 16))

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
