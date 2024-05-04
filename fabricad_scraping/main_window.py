from pathlib import Path

from PySide6 import QtCore, QtWidgets

from fabricad_scraping.browser import Browser


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.browser = Browser(headless=False)
        self.browser.make_login()

        self.setFixedSize(600, 200)
        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())

        self.message_box = QtWidgets.QMessageBox()

        self.download_folder_label = QtWidgets.QLabel('Pasta para Download')
        self.download_folder_input = QtWidgets.QLineEdit()
        self.download_folder_input.setReadOnly(True)
        self.download_folder_button = QtWidgets.QPushButton('Selecionar')
        self.download_folder_button.clicked.connect(
            self.choose_download_folder
        )
        self.download_folder_layout = QtWidgets.QHBoxLayout()
        self.download_folder_layout.addWidget(self.download_folder_input)
        self.download_folder_layout.addWidget(self.download_folder_button)

        self.discipline_label = QtWidgets.QLabel('Disciplina')
        self.discipline_combobox = QtWidgets.QComboBox()
        self.discipline_combobox.addItems(self.browser.get_disciplines())
        self.discipline_layout = QtWidgets.QHBoxLayout()
        self.discipline_layout.addWidget(self.discipline_label)
        self.discipline_layout.addWidget(self.discipline_combobox)

        self.course_label = QtWidgets.QLabel('Curso')
        self.course_combobox = QtWidgets.QComboBox()
        self.course_combobox.addItems(
            self.browser.get_courses(self.discipline_combobox.currentText())
        )
        self.course_layout = QtWidgets.QHBoxLayout()
        self.course_layout.addWidget(self.course_label)
        self.course_layout.addWidget(self.course_combobox)

        self.discipline_combobox.currentTextChanged.connect(
            self.update_course_combobox
        )

        self.download_course_button = QtWidgets.QPushButton('Fazer Download')
        self.download_course_button.clicked.connect(self.download_course)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.download_folder_label)
        self.main_layout.addLayout(self.download_folder_layout)
        self.main_layout.addLayout(self.discipline_layout)
        self.main_layout.addLayout(self.course_layout)
        self.main_layout.addWidget(self.download_course_button)

    @QtCore.Slot()
    def choose_download_folder(self):
        self.download_folder_input.setText(
            QtWidgets.QFileDialog.getExistingDirectory()
        )

    @QtCore.Slot()
    def update_course_combobox(self, text):
        self.course_combobox.clear()
        self.course_combobox.addItems(self.browser.get_courses(text))

    @QtCore.Slot()
    def download_course(self):
        self.browser.download_course(
            self.discipline_combobox.currentText(),
            self.course_combobox.currentText(),
            Path(self.download_folder_input.text()),
        )
        self.message_box.setText('Finalizado!')
        self.message_box.show()
