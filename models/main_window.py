import re
import os
import json
import bz2

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPlainTextEdit, QMenu, QInputDialog, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QEvent


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UI_PATH = os.path.join(BASE_DIR, 'ui/MainWindow.ui')
ICON_PATH = os.path.join(BASE_DIR, 'fastnote.ico')


class MainWindow(QMainWindow):
    saveDataSignal = pyqtSignal()
    moveTabSignal = pyqtSignal(int)

    def __init__(self, settings_path):
        self.path = settings_path
        self.lastDataJson = None
        self.loading = False
        self.lastSaveDir = os.path.expanduser('~')
        self.pid = os.getpid()

        super().__init__()
        # self.checkPid()
        # self.savePid()

        self.ui = self.initUI()

        self.setWindowTitle('Fastnote')
        self.setWindowIcon(QIcon(ICON_PATH))

        self.initTabWidget()

    def __del__(self):
        self.ui = None

    def initUI(self):
        ui = uic.loadUi(UI_PATH, self)

        ui.tabWidget.currentChanged.connect(self.changeTabEvent)
        self.saveDataSignal.connect(self.saveEvent, Qt.QueuedConnection)
        self.moveTabSignal.connect(self.moveTabEvent, Qt.QueuedConnection)

        return ui

    def event(self, e):
        if e.type() == QEvent.UpdateRequest:
            self.saveDataSignal.emit()

        if e.type() == QEvent.KeyPress:
            modifiers = int(e.modifiers())
            key = e.key()
            if modifiers and modifiers == Qt.ALT and \
                    key in (Qt.Key_Left, Qt.Key_Right):
                direction = 1 if key == Qt.Key_Right else -1
                self.moveTabSignal.emit(direction)

        return super().event(e)

    # def closeEvent(self, e):
    #     self.deletePid()

    def changeTabEvent(self, index):
        count = self.ui.tabWidget.count()

        if not self.loading and index == count - 1:
            title = self.getNewUntitledTitle()
            self.addTab(title, '')

        self.saveDataSignal.emit()

    def saveEvent(self):
        data = {
            "tabs": [],
            "geom": {
                "width": self.geometry().width(),
                "height": self.geometry().height(),
                "left": self.geometry().left(),
                "top": self.geometry().top()
            },
            "fullscreen": self.isFullScreen(),
            "current_index": self.ui.tabWidget.currentIndex()
        }

        count = self.ui.tabWidget.count()
        for i in range(count - 1):
            title, text = self.getTabData(i)
            data["tabs"].append({
                'title': title,
                'text': text
            })

        self.saveData(data)

    def moveTabEvent(self, direction):
        currentIndex = self.ui.tabWidget.currentIndex()

        nextIndex = None

        if direction > 0 and currentIndex < self.ui.tabWidget.count() - 2:
            nextIndex = currentIndex + 1
        if direction < 0 and currentIndex > 0:
            nextIndex = currentIndex - 1

        if nextIndex is not None:
            self.swapTabs(currentIndex, nextIndex)
            self.ui.tabWidget.setCurrentIndex(nextIndex)
            self.ui.tabWidget.widget(nextIndex).children()[1].setFocus()
            self.saveDataSignal.emit()

    def contextMenuEvent(self, event):
        tabIndex = self.getClickedTabIndex(event.pos())

        if tabIndex is not None and tabIndex < self.ui.tabWidget.count() - 1:
            menu = QMenu(self)

            renameAction = menu.addAction("Rename")
            saveasAction = menu.addAction("Save as...")
            removeAction = menu.addAction("Remove")

            action = menu.exec_(self.mapToGlobal(event.pos()))

            if action == renameAction:
                self.renameTabSlot(tabIndex)

            elif action == saveasAction:
                self.saveTabAction(tabIndex)

            elif action == removeAction:
                self.removeTabSlot(tabIndex)

    def initTabWidget(self):
        data = self.loadData()

        if data is not None:
            if "fullscreen" in data:
                if data["fullscreen"]:
                    self.showMaximized()

                elif "geom" in data:
                    geom = self.geometry()
                    geom.setLeft(data["geom"]["left"])
                    geom.setTop(data["geom"]["top"])
                    geom.setWidth(data["geom"]["width"])
                    geom.setHeight(data["geom"]["height"])
                    self.setGeometry(geom)

            for tab in data["tabs"]:
                self.addTab(
                    title=tab['title'],
                    text=tab['text']
                )

            currentIndex = data.get("current_index", 0)
            self.ui.tabWidget.setCurrentIndex(currentIndex)
            self.ui.tabWidget.widget(currentIndex).children()[1].setFocus()

        if self.ui.tabWidget.count() == 1:
            title = self.getNewUntitledTitle()
            self.addTab(title, '')

    def saveData(self, data):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        dataPath = os.path.join(self.path, "data")

        dataJson = json.dumps(data)

        if dataJson != self.lastDataJson:
            self.lastDataJson = dataJson
            dataCompressed = bz2.compress(dataJson.encode())

            with open(dataPath, "wb") as f:
                f.write(dataCompressed)

    def loadData(self):
        dataPath = os.path.join(self.path, "data")

        data = None

        if os.path.exists(dataPath):
            with open(dataPath, "rb") as f:
                dataCompressed = f.read()
                data = json.loads(bz2.decompress(dataCompressed).decode())

        return data

    def addTab(self, title, text):
        self.loading = True

        newTab = QWidget(self)

        layout = QVBoxLayout()
        newTab.setLayout(layout)

        newTextEdit = QPlainTextEdit(newTab)
        widgetGeometry = self.ui.tabWidget.geometry()
        widgetGeometry.setTop(0)
        widgetGeometry.setLeft(0)
        newTextEdit.setGeometry(widgetGeometry)
        newTextEdit.setPlainText(text)
        layout.addWidget(newTextEdit)

        count = self.ui.tabWidget.count()

        newTabIndex = self.ui.tabWidget.addTab(newTab, title)

        self.ui.tabWidget.tabBar().moveTab(count - 1, newTabIndex)
        self.ui.tabWidget.setCurrentIndex(count - 1)

        self.loading = False

    def getNewUntitledTitle(self):
        count = self.ui.tabWidget.count()

        untitledNums = set()
        for index in range(count):
            text = self.ui.tabWidget.tabText(index)

            untitledMatch = re.match(r'^Untitled( \((\d+)\))?$', text)
            if untitledMatch is not None:
                num = int(untitledMatch.group(2)) \
                    if untitledMatch.group(2) is not None else 1
                untitledNums.add(num)

        newNum = 1
        while newNum in untitledNums:
            newNum += 1

        return "Untitled (%d)" % newNum if newNum != 1 else "Untitled"

    def getTabData(self, index):
        title = self.ui.tabWidget.tabText(index)
        text = self.ui.tabWidget.widget(index).children()[1].toPlainText()
        return title, text

    def setTabData(self, index, title, text):
        self.ui.tabWidget.setTabText(index, title)
        self.ui.tabWidget.widget(index).children()[1].setPlainText(text)

    def renameTabSlot(self, tabIndex):
        oldTitle = self.ui.tabWidget.tabText(tabIndex)

        newTitle, ok = QInputDialog.getText(
            self,
            "Rename",
            "Enter a new title for the tab:",
            text=oldTitle
        )

        if ok:
            self.ui.tabWidget.setTabText(tabIndex, newTitle)
            self.saveDataSignal.emit()

    def saveTabAction(self, tabIndex):
        title = self.ui.tabWidget.tabText(tabIndex)

        filePath = os.path.join(
            self.lastSaveDir,
            title + '.txt'
        )

        filePath = QFileDialog.getSaveFileName(self, 'Save', filePath)[0]

        self.lastSaveDir = os.path.dirname(filePath)

        if filePath:
            text = self.ui.tabWidget.widget(tabIndex).children()[1].toPlainText()
            with open(filePath, 'w') as f:
                f.write(text)

    def removeTabSlot(self, tabIndex):
        title = self.ui.tabWidget.tabText(tabIndex)

        answer = QMessageBox.question(
            self,
            "Remove",
            "Are you sure to remove '{0}'?".format(title),
            QMessageBox.Yes,
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:
            currentIndex = self.ui.tabWidget.currentIndex()

            if tabIndex == currentIndex:
                if tabIndex > 0:
                    self.ui.tabWidget.setCurrentIndex(tabIndex - 1)
                else:
                    self.ui.tabWidget.setCurrentIndex(tabIndex + 1)

            self.ui.tabWidget.removeTab(tabIndex)

            if self.ui.tabWidget.count() == 1:
                self.addTabEvent()

            self.saveDataSignal.emit()

    def getClickedTabIndex(self, pos):
        tabBar = self.ui.tabWidget.tabBar()

        globalPos = self.mapToGlobal(pos)
        posInTabBar = tabBar.mapFromGlobal(globalPos)

        count = self.ui.tabWidget.count()

        for i in range(count):
            if tabBar.tabRect(i).contains(posInTabBar):
                return i

        return None

    def swapTabs(self, index1, index2):
        tabData1 = self.getTabData(index1)
        tabData2 = self.getTabData(index2)
        self.setTabData(index1, *tabData2)
        self.setTabData(index2, *tabData1)

    def checkPid(self):
        pidPath = os.path.join(self.path, 'pid')
        if os.path.exists(pidPath):
            raise Exception("pid-file found")

    def savePid(self):
        pidPath = os.path.join(self.path, 'pid')
        with open(pidPath, 'w') as f:
            f.write(str(self.pid))

    def deletePid(self):
        pidPath = os.path.join(self.path, 'pid')
        os.remove(pidPath)
