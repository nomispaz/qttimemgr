import sys
from subprocess import run
from time import sleep

from PyQt6.QtCore import QSize, Qt, QProcess, QByteArray
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
        QApplication,
        QPushButton,
        QMainWindow,
        QVBoxLayout,
        QGridLayout,
        QWidget,
        QPlainTextEdit,
        QInputDialog,
        QLineEdit,
        QDialogButtonBox,
        QCompleter
)

class QtTimeMgrWindow(QMainWindow):
    def setupUI(self):
        #create widgets
        #input field
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Enter project")
        #completer
        self.lProjects = ['Test1', 'Abc']
        self.cProject = QCompleter(self.lProjects,self)
        self.cProject.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.input.setCompleter(self.cProject)
        #start timetracking
        self.bStart = QPushButton("Start",self)
        #end timetracking
        self.bEnd = QPushButton("End",self)
        
        
        #resize widgets (x/y coordinates)
        self.input.resize(300,30)

        #order Layout (x/y coordinates)
        self.bStart.move(0,0)
        self.input.move(0,50)
        self.bEnd.move(100,0)
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("nomispaz Time Manager")
        self.setupUI()
        


###############################################################################

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