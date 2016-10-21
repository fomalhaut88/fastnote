import os
import sys
import subprocess as sp

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from models.MainWindow import MainWindow



path = os.path.join(
    os.path.expanduser("~"),
    ".fastnote"
)



def already_started():
    if sys.platform == "win32":
        return False

    else:
        psaux_info = sp.Popen("ps aux | grep \"fastnote\" | grep \"Sl\" | grep -v grep", shell = True, stdout=sp.PIPE).communicate()[0]
        return bool(psaux_info)



if __name__ == "__main__":
    if already_started():
        print "fastnote is already started"

    else:
        app = QApplication(sys.argv)
        app.setApplicationName('FastNote')

        window = MainWindow(path = path)
        window.setWindowTitle('FastNote')
        window.show()

        QObject.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

        sys.exit(app.exec_())
