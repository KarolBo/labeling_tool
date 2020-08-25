from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from glob import glob
from os.path import join, abspath
from PyQt5.QtCore import pyqtSlot
import sys
from settings import Settings, handle_exceptions


class Tutorial:
    def __init__(self, parent):
        self.folder = getattr(sys, '_MEIPASS', abspath('.'))
        self.project_creator_dialog = None
        self.settings = Settings()
        self.start_project = lambda: parent.start_project(self.settings)

        self.step_1()

    @handle_exceptions
    def step_1(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_1.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()
        self.project_creator_dialog.activateWindow()

        def on_next_click():
            self.settings.project_name = self.project_creator_dialog.line_proj_name.text()
            self.settings.author = self.project_creator_dialog.line_auth_name.text()
            self.settings.institution = self.project_creator_dialog.line_institution.text()

            self.settings.eval_cc = self.project_creator_dialog.checkbox_cc.isChecked()
            self.settings.eval_mlo = self.project_creator_dialog.checkbox_mlo.isChecked()
            self.settings.eval_mammo = self.project_creator_dialog.checkbox_mammo.isChecked()
            self.settings.eval_tomo = self.project_creator_dialog.checkbox_tomo.isChecked()

            self.settings.decode = self.project_creator_dialog.checkbox_decode.isChecked()

            self.step_2()

        def set_extension(ext):
            self.settings.file_extension = ext

        self.project_creator_dialog.radio_dicom.toggled.connect(lambda: set_extension('dcm'))
        self.project_creator_dialog.radio_dicom.toggled.connect(lambda: set_extension('jpg'))

        self.project_creator_dialog.button_browse_project.clicked.connect(self.set_project_folder)
        self.project_creator_dialog.button_browse_data.clicked.connect(self.set_data_folder)

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next_click)

    @handle_exceptions
    def set_project_folder(self, _):
        self.project_creator_dialog.setVisible(False)
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.settings.project_folder = str(file_dialog.getExistingDirectory(self.project_creator_dialog))
        self.project_creator_dialog.activateWindow()
        self.project_creator_dialog.setVisible(True)
        self.project_creator_dialog.line_proj_folder.setText(self.settings.project_folder)

        self.eval_step_1()

    @handle_exceptions
    def set_data_folder(self, _):
        self.project_creator_dialog.setVisible(False)
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.settings.data_folder = str(file_dialog.getExistingDirectory(self.project_creator_dialog))
        self.project_creator_dialog.activateWindow()
        self.project_creator_dialog.setVisible(True)
        self.project_creator_dialog.line_data_folder.setText(self.settings.data_folder)

        self.eval_step_1()

    @handle_exceptions
    def eval_step_1(self):
        pattern = join('**', '*.' + self.settings.file_extension)
        path = join(self.settings.data_folder, pattern)
        image_list = glob(path, recursive=True)

        is_ready = bool(self.settings.project_folder)
        is_ready = is_ready and len(image_list)

        self.project_creator_dialog.button_next.setEnabled(is_ready)

    @pyqtSlot()
    @handle_exceptions
    def step_2(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_2.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()
        self.project_creator_dialog.activateWindow()

        def on_class_check(state):
            self.project_creator_dialog.label_classes.setEnabled(state)
            self.project_creator_dialog.comboBox.setEnabled(state)
            self.project_creator_dialog.checkbox_copy.setEnabled(state)

        def on_object_check(state):
            self.project_creator_dialog.radio_point.setEnabled(state)
            self.project_creator_dialog.radio_square.setEnabled(state)
            self.project_creator_dialog.combo_obj_num.setEnabled(state)
            self.project_creator_dialog.label_2.setEnabled(state)
            self.project_creator_dialog.check_unlimited.setEnabled(state)

        def on_unlimited_check(state):
            self.project_creator_dialog.combo_obj_num.setEnabled(not state)

        def on_next_click():
            self.settings.copy_files = self.project_creator_dialog.checkbox_copy.isChecked()

            next_step = self.finito
            if self.project_creator_dialog.checkbox_object.isChecked():
                if not self.project_creator_dialog.check_unlimited.isChecked():
                    next_step = self.step_4
                    self.settings.object_names = (self.project_creator_dialog.combo_obj_num.currentIndex() + 1) * ['']

                if self.project_creator_dialog.radio_point.isChecked():
                    self.settings.object_detection_mode = 1
                else:
                    self.settings.object_detection_mode = 2
            else:
                self.settings.object_detection_mode = 0

            if self.project_creator_dialog.check_class.isChecked():
                self.settings.class_labels = (self.project_creator_dialog.comboBox.currentIndex() + 2) * ['']
                next_step = self.step_3

            next_step()

        self.project_creator_dialog.check_class.stateChanged.connect(on_class_check)
        self.project_creator_dialog.checkbox_object.stateChanged.connect(on_object_check)
        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.check_unlimited.clicked.connect(on_unlimited_check)
        self.project_creator_dialog.button_next.clicked.connect(on_next_click)

    @handle_exceptions
    def step_3(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_3_4.ui'))
        self.project_creator_dialog.setWindowFlags(self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint
                                                   | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()
        self.project_creator_dialog.activateWindow()

        self.project_creator_dialog.tableWidget.setRowCount(len(self.settings.class_labels))
        for i in range(len(self.settings.class_labels)):
            item = QTableWidgetItem(str(i))
            item.setFlags(item.flags() | ~Qt.ItemIsEditable)
            self.project_creator_dialog.tableWidget.setItem(i, 0, item)
            item = QTableWidgetItem('class {}'.format(i))
            self.project_creator_dialog.tableWidget.setItem(i, 1, item)

        def on_next():
            for j in range(len(self.settings.class_labels)):
                label = self.project_creator_dialog.tableWidget.item(j, 1).text()
                self.settings.class_labels[j] = label
            if self.settings.object_detection_mode and self.settings.object_names:
                self.step_4()
            else:
                self.finito()

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next)

    @handle_exceptions
    def step_4(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_3_4.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()
        self.project_creator_dialog.activateWindow()

        self.project_creator_dialog.tableWidget.setRowCount(len(self.settings.object_names))
        for i in range(len(self.settings.object_names)):
            item = QTableWidgetItem(str(i))
            item.setFlags(item.flags() | ~Qt.ItemIsEditable)
            self.project_creator_dialog.tableWidget.setItem(i, 0, item)
            item = QTableWidgetItem('object {}'.format(i))
            self.project_creator_dialog.tableWidget.setItem(i, 1, item)

        def on_next():
            for j in range(len(self.settings.object_names)):
                obj = self.project_creator_dialog.tableWidget.item(j, 1).text()
                self.settings.object_names[j] = obj
            self.finito()

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next)

    @handle_exceptions
    def finito(self):
        self.project_creator_dialog = None
        self.start_project()
