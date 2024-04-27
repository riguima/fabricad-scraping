import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from fabricad_scraping.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication([])
    apply_stylesheet(app, 'dark_blue.xml')
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
