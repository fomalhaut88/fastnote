import os
import sys
import logging
from argparse import ArgumentParser

from PyQt5.QtWidgets import QApplication

from models.main_window import MainWindow


settings_path = os.path.join(
    os.path.expanduser("~"),
    ".fastnote"
)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--debug", action='store_true', default=False
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName('Fastnote')

    if args.debug:
        window = MainWindow(settings_path)
        window.show()
        sys.exit(app.exec_())

    else:
        try:
            window = MainWindow(settings_path)
            window.show()
            code = sys.exit(app.exec_())
        except Exception as exc:
            logging.critical(exc)
            sys.exit(1)
        else:
            sys.exit(code)
