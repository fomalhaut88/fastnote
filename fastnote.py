__version__ = "2.1"

import os
import sys
import re
import subprocess as sp

if sys.platform == "win32":
    import wmi

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from models.MainWindow import MainWindow



path = os.path.join(
    os.path.expanduser("~"),
    ".fastnote"
)



def already_started():
    if sys.platform == "win32":
        c = wmi.WMI()
        pids = [
            (p.ProcessId, p.Name) for p in c.Win32_process()
            if re.match(r'fastnote.*?\.exe', p.Name)
        ]
        return len(pids) > 2

    else:
        psaux_info = sp.Popen("ps aux | grep \"fastnote\" | grep \"Sl\" | grep -v grep", shell = True, stdout=sp.PIPE).communicate()[0]
        return bool(psaux_info)



if __name__ == "__main__":
    if len(sys.argv) > 1 and "--version" in sys.argv[1:]:
        print __version__
        sys.exit(0)

    if already_started():
        print "fastnote is already started"

    else:
        app = QApplication(sys.argv)
        app.setApplicationName('FastNote')

        window = MainWindow(path=path)
        window.setWindowTitle('FastNote')
        window.show()

        QObject.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

        sys.exit(app.exec_())
