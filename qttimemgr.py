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
        QCompleter
)

class QtTimeMgrWindow(QMainWindow):
    def addProject(self):
        writeFile("projects",self.iProject.text())
        #update projectlist in GUI
        self.lProjects = readFile("projects")
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.iProject.setCompleter(self.cProject)
        self.printMessage("Project " + self.iProject.text() + " saved.")

    def startTimer(self):
        self.curProject = self.iProject.text()
        self.startTime = datetime.now().strftime("%H:%M:%S")
        self.startTimestamp = datetime.timestamp(datetime.now())
        #self.curYear = date.today().year
        #self.curMonth = date.today().month
        self.curWeek = date.today().isocalendar()[1]
        self.curDay = date.today()
        self.printMessage(
            str(self.startTime)
            + " : "
            + self.curProject
            + " , Tracking started "
            )
    def endTimer(self):
        self.endTime = datetime.now().strftime("%H:%M:%S")
        self.endTimestamp = datetime.timestamp(datetime.now())
        self.printMessage(
            str(self.endTime)
            + " : "
            + self.curProject
            + " , Tracking ended. Duration: " + 
                str(
                    timedelta(seconds=
                        floor(self.endTimestamp-self.startTimestamp)
                    )
                )
            )
        
        curRow = writeFile("timetracking", self.curProject + ";" + str(self.curDay) + ";" + str(self.curWeek) + ";" + str(floor(self.startTimestamp)) + ";" + str(ceil(self.endTimestamp)))
        #write idxYear
        writeIndex("idxYear", str(self.curDay.year), str(curRow))
        #write idxMonth
        writeIndex("idxMonth", str(self.curDay.year) +  "-" + str(self.curDay.month), str(curRow))
        #write idxWeek
        writeIndex("idxWeek", str(self.curDay.year) +  "-" + str(self.curWeek), str(curRow))

    #print to Textbox
    def printMessage(self, s):
        self.oMainTextField.appendPlainText(s)

    def setupUI(self):
        #create widgets
        #project input field with completer
        self.iProject = QLineEdit(self)
        self.iProject.setPlaceholderText("Enter project")
        #completer
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
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

        #output window
        self.oMainTextField = QPlainTextEdit(self)
        self.oMainTextField.setReadOnly(True)
        
        #resize widgets (x/y coordinates)
        #project input field
        self.iProject.resize(300, 30)
        self.oMainTextField.resize(1000, 1000)

        #order Layout (x/y coordinates)
        self.bStart.move(0, 0)
        self.iProject.move(0, 50)
        self.bNewProject.move(310, 50)
        self.bEnd.move(100, 0)
        self.oMainTextField.move(0, 100)

    def __init__(self):
        super().__init__()

        #init variables
        self.curProject = ""
        self.startTime = 0
        self.startTimestamp = 0
        self.endTime = 0
        self.endTimestamp = 0
        self.curYear = 0
        self.curMonth = 0
        self.curWeek = 0
        self.curDay = 0

        #setup projects
        self.lProjects = readFile("projects")

        self.setWindowTitle("nomispaz Time Manager")
        self.setupUI()
        


###############################################################################

def readFile(filename):
    vCurDir = os.getcwd()
    vDataPath = vCurDir+"/qttimemgr/data/"
    file = open(vDataPath+filename, "r")
    splitFile = []
    for line in file.readlines():
        splitFile.append(line.strip())
    file.close()
    return splitFile

def readFileIdx(filename):
    vCurDir = os.getcwd()
    vDataPath = vCurDir+"/qttimemgr/data/"
    file = open(vDataPath+filename, "r")
    dSplitFile = {0:0}
    for line in file.readlines():
        lineSplit = line.strip().split(";")
        dSplitFile[lineSplit[0]] = lineSplit[1]
    file.close()
    return dSplitFile

def writeFile(filename, text):
    vCurDir = os.getcwd()
    vDataPath = vCurDir+"/qttimemgr/data/"
    file = open(vDataPath+filename, "r+")
    vFileLength = len(file.readlines())
    #jump to end of file
    file.read()
    file.write("\n"+str(text))
    file.close()

    #return new length of file
    return vFileLength

def writeIndex(filename, idxValue, idxRow):
    #index year
    dCurIdx = readFileIdx(filename)
    #if year/month/week is new, write index
    try:
        dCurIdx[idxValue]
    except:
        writeFile(filename, idxValue + ";" + idxRow)

def main():

    # You need one (and only one) QApplication instance per application.
    # Pass in sys.argv to allow command line arguments for your app.
    # If you know you won't use command line arguments QApplication([]) works too.
    qttimemgrApp = QApplication(sys.argv)
    qttimemgrApp.setFont(QFont('Awesome', 20))

    # Create a Qt widget, which will be our window.
    qttimemgrWindow = QtTimeMgrWindow()
    # IMPORTANT!!!!! Windows are hidden by default.
    qttimemgrWindow.show()  

    # Start the event loop.
    sys.exit(qttimemgrApp.exec())

if __name__ == "__main__":
    main()
