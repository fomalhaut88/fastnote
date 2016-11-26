import re
import os
import json
import bz2

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *



BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UI_PATH = os.path.join(BASE_DIR, 'ui/MainWindow.ui')
ICON_PATH = os.path.join(BASE_DIR, 'fastnote.ico')



(UI_cls, Parent_cls) = uic.loadUiType(UI_PATH)


class MainWindow(Parent_cls):
    def __init__(self, parent=None, path=None):
        assert path is not None

        self.path = path

        Parent_cls.__init__(self, parent)

        self.ui = UI_cls()
        self.ui.setupUi(self)

        self.setWindowTitle('Fastnote')
        self.setWindowIcon(QIcon(ICON_PATH))

        self.connect(
            self.ui.tabWidget,
            SIGNAL("currentChanged(int)"),
            self.addTabEvent
        )
        self.connect(
            self,
            SIGNAL("saveData"),
            self.save
        )
        self.connect(
            self,
            SIGNAL("moveTab(int)"),
            self.moveTabEvent
        )

        self.initTabWidget()


    def __del__(self):
        self.ui = None


    def event(self, e):
        if e.type() in (QEvent.KeyPress, QEvent.KeyRelease, QEvent.Resize, QEvent.UpdateRequest):
            self.emit(SIGNAL("saveData"))
        if e.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            modifiers = int(e.modifiers())
            key = e.key()
            if modifiers and modifiers == Qt.ALT and key in (Qt.Key_Left, Qt.Key_Right):
                print "move signal"
                direction = 1 if key == Qt.Key_Right else -1
                self.emit(SIGNAL("moveTab(int)"), direction)
        return Parent_cls.event(self, e)


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
                self.addTabEvent(
                    title=tab['title'],
                    text=tab['text'],
                    loaded=True
                )

            currentIndex = data["current_index"] if "current_index" in data else 0
            self.ui.tabWidget.setCurrentIndex(currentIndex)
            self.ui.tabWidget.widget(currentIndex).children()[1].setFocus()

        if self.ui.tabWidget.count() == 1:
            self.addTabEvent()


    def save(self):
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
        for i in xrange(count - 1):
            title, text = self.getTabData(i)
            data["tabs"].append({
                'title': title,
                'text': text
            })

        self.saveData(data)


    def saveData(self, data):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        dataPath = os.path.join(self.path, "data")
        dataPathJson = os.path.join(self.path, "data.json")

        with open(dataPath, "wb") as f:
            dataCompressed = bz2.compress(json.dumps(data))
            f.write(dataCompressed)

        if os.path.exists(dataPathJson):
            os.remove(dataPathJson)


    def loadData(self):
        dataPath = os.path.join(self.path, "data")
        dataPathJson = os.path.join(self.path, "data.json")

        data = None

        if os.path.exists(dataPath):
            with open(dataPath, "rb") as f:
                dataCompressed = f.read()
                data = json.loads(bz2.decompress(dataCompressed))

        elif os.path.exists(dataPathJson):
            with open(dataPathJson, "rb") as f:
                data = json.load(f)

        return data


    def getTabData(self, index):
        title = unicode(self.ui.tabWidget.tabText(index))
        text = unicode(self.ui.tabWidget.widget(index).children()[1].toPlainText())
        return title, text


    def setTabData(self, index, title, text):
        self.ui.tabWidget.setTabText(index, title)
        self.ui.tabWidget.widget(index).children()[1].setPlainText(text)


    def addTabEvent(self, changedIndex=None, title=None, text="", loaded=False):
        # addTabIndex
        addTabIndex = self.ui.tabWidget.currentIndex()
        count = self.ui.tabWidget.count()

        if title is not None or addTabIndex == count - 1:
            # newTab
            newTab = QWidget(self)

            # layout
            layout = QVBoxLayout()
            layout.setMargin(0)
            newTab.setLayout(layout)

            # newTextEdit with geometry
            newTextEdit = QPlainTextEdit(newTab)
            widgetGeometry = self.ui.tabWidget.geometry()
            widgetGeometry.setTop(0)
            widgetGeometry.setLeft(0)
            newTextEdit.setGeometry(widgetGeometry)
            newTextEdit.setPlainText(text)
            layout.addWidget(newTextEdit)

            # new title
            if title is None:
                title = self.getNewUntitledTitle()

            # adding, replacing and setting the current tab
            newTabIndex = self.ui.tabWidget.addTab(newTab, title)
            self.ui.tabWidget.tabBar().moveTab(count - 1, newTabIndex)
            self.ui.tabWidget.setCurrentIndex(count - 1)

            if loaded:
                self.ui.tabWidget.setCurrentIndex(0)
                self.ui.tabWidget.widget(0).children()[1].setFocus()

        # saving
        if not loaded:
            self.emit(SIGNAL("saveData"))


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


    def renameTabSlot(self, tabIndex):
        oldTitle = self.ui.tabWidget.tabText(tabIndex)

        newTitle, ok = QInputDialog.getText(
            self,
            u"Rename",
            u"Enter a new title for the tab:",
            text = oldTitle
        )

        if ok:
            self.ui.tabWidget.setTabText(tabIndex, newTitle)
            self.emit(SIGNAL("saveData"))


    def saveTabAction(self, tabIndex):
        title = unicode(self.ui.tabWidget.tabText(tabIndex))

        filePath = os.path.join(
            os.path.expanduser('~'),
            title + '.txt'
        )

        filePath = unicode(QFileDialog.getSaveFileName(self, 'Save', filePath))

        if filePath:
            text = unicode(self.ui.tabWidget.widget(tabIndex).children()[1].toPlainText())
            with open(filePath, 'w') as f:
                f.write(text.encode('utf8'))


    def removeTabSlot(self, tabIndex):
        title = unicode(self.ui.tabWidget.tabText(tabIndex))

        answer = QMessageBox.question(
            self,
            u"Remove",
            u"Are you sure to remove '{0}'?".format(title),
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

            self.emit(SIGNAL("saveData"))


    def getClickedTabIndex(self, pos):
        tabBar = self.ui.tabWidget.tabBar()

        globalPos = self.mapToGlobal(pos)
        posInTabBar = tabBar.mapFromGlobal(globalPos)

        count = self.ui.tabWidget.count()

        for i in xrange(count):
            if tabBar.tabRect(i).contains(posInTabBar):
                return i

        return None


    def getNewUntitledTitle(self):
        count = self.ui.tabWidget.count()

        untitledNums = set()
        for index in xrange(count):
            text = self.ui.tabWidget.tabText(index)

            untitledMatch = re.match(r'^Untitled( \((\d+)\))?$', text)
            if untitledMatch is not None:
                num = int(untitledMatch.group(2)) if untitledMatch.group(2) is not None else 1
                untitledNums.add(num)

        newNum = 1
        while newNum in untitledNums:
            newNum += 1

        return "Untitled (%d)" % newNum if newNum != 1 else "Untitled"


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
            self.emit(SIGNAL("saveData"))


    def swapTabs(self, index1, index2):
        tabData1 = self.getTabData(index1)
        tabData2 = self.getTabData(index2)
        self.setTabData(index1, *tabData2)
        self.setTabData(index2, *tabData1)
