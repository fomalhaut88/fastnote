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
    pid = os.getpid()
    psaux_info = sp.Popen("ps aux | grep \"fastnote\" | grep -v grep | awk '{ print $2, $4 }'", shell = True, stdout=sp.PIPE).communicate()[0].strip().split('\n')
    psaux_info = map(lambda l: l.split(), psaux_info)
    psaux_info = filter(lambda e: e[1] != "0.0", psaux_info)
    started_pids = set(map(lambda e: int(e[0]), psaux_info))
    started_pids.remove(pid)
    return bool(started_pids)



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
