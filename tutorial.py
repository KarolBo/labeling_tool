from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from glob import glob
from os.path import join, abspath
from PyQt5.QtCore import pyqtSlot
import json
import functools
import sys


def handle_exceptions(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            with open('errors.log', 'a+') as f:
                f.write('Exception in {}: {}\n'.format(func.__name__, e))
            return None
    return func_wrapper


class Tutorial:
    def __init__(self):
        self.folder = getattr(sys, '_MEIPASS', abspath('.'))
        self.project_creator_dialog = None
        self.project_name = ''
        self.author = ''
        self.institution = ''
        self.project_folder = ''
        self.data_folder = ''
        self.class_labels = []
        self.object_detection_mode = 0
        self.object_names = []
        self.img_idx = 0
        self.eval_cc = self.eval_mlo = self.eval_mammo = self.eval_tomo = True
        self.copy_files = False
        self.file_extension = 'dcm'

        self.step_1()

    @handle_exceptions
    def step_1(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_1.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                                                      | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()

        def on_filter_check(_):
            self.eval_cc = self.project_creator_dialog.checkbox_cc.isChecked()
            self.eval_mlo = self.project_creator_dialog.checkbox_mlo.isChecked()
            self.eval_mammo = self.project_creator_dialog.checkbox_mammo.isChecked()
            self.eval_tomo = self.project_creator_dialog.checkbox_thomo.isChecked()

        def on_next_click():
            self.project_name = self.project_creator_dialog.line_proj_name.text()
            self.author = self.project_creator_dialog.line_auth_name.text()
            self.institution = self.project_creator_dialog.line_institution.text()
            self.step_2()

        def set_extension(ext):
            self.file_extension = ext

        self.project_creator_dialog.radio_dicom.toggled.connect(lambda: set_extension('dcm'))
        self.project_creator_dialog.radio_dicom.toggled.connect(lambda: set_extension('jpg'))

        self.project_creator_dialog.checkbox_cc.stateChanged.connect(on_filter_check)
        self.project_creator_dialog.checkbox_mlo.stateChanged.connect(on_filter_check)
        self.project_creator_dialog.checkbox_mammo.stateChanged.connect(on_filter_check)
        self.project_creator_dialog.checkbox_thomo.stateChanged.connect(on_filter_check)

        self.project_creator_dialog.button_browse_project.clicked.connect(self.set_project_folder)
        self.project_creator_dialog.button_browse_data.clicked.connect(self.set_data_folder)

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next_click)

    @handle_exceptions
    def set_project_folder(self, _):
        self.project_creator_dialog.setVisible(False)
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.project_folder = str(file_dialog.getExistingDirectory(self.project_creator_dialog))
        self.project_creator_dialog.setVisible(True)
        self.project_creator_dialog.line_proj_folder.setText(self.project_folder)

        self.eval_step_1()

    @handle_exceptions
    def set_data_folder(self, _):
        self.project_creator_dialog.setVisible(False)
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.data_folder = str(file_dialog.getExistingDirectory(self.project_creator_dialog))
        self.project_creator_dialog.setVisible(True)
        self.project_creator_dialog.line_data_folder.setText(self.data_folder)

        self.eval_step_1()

    @handle_exceptions
    def eval_step_1(self):
        pattern = join('**', '*.' + self.file_extension)
        path = join(self.data_folder, pattern)
        image_list = glob(path, recursive=True)

        is_ready = bool(self.project_folder)
        is_ready = is_ready and bool(image_list)

        print(is_ready)

        self.project_creator_dialog.button_next.setEnabled(is_ready)

    @pyqtSlot()
    @handle_exceptions
    def step_2(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_2.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()

        def on_class_check(state):
            self.project_creator_dialog.label_classes.setEnabled(state)
            self.project_creator_dialog.comboBox.setEnabled(state)
            self.project_creator_dialog.checkbox_copy.setEnabled(state)

        def on_object_check(state):
            self.project_creator_dialog.radio_point.setEnabled(state)
            self.project_creator_dialog.radio_square.setEnabled(state)
            self.project_creator_dialog.combo_obj_num.setEnabled(state)
            self.project_creator_dialog.label_2.setEnabled(state)

        def on_next_click():
            self.copy_files = self.project_creator_dialog.checkbox_copy.isChecked()

            next_step = self.save_settings
            if self.project_creator_dialog.checkbox_object.isChecked():
                next_step = self.step_4
                self.object_names = (self.project_creator_dialog.combo_obj_num.currentIndex() + 1) * ['']

                if self.project_creator_dialog.radio_point.isChecked():
                    self.object_detection_mode = 1
                else:
                    self.object_detection_mode = 2
            else:
                self.object_detection_mode = 0

            if self.project_creator_dialog.check_class.isChecked():
                self.class_labels = (self.project_creator_dialog.comboBox.currentIndex() + 2) * ['']
                next_step = self.step_3

            next_step()

        self.project_creator_dialog.check_class.stateChanged.connect(on_class_check)
        self.project_creator_dialog.checkbox_object.stateChanged.connect(on_object_check)

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next_click)

    @handle_exceptions
    def step_3(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_3_4.ui'))
        self.project_creator_dialog.setWindowFlags(self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint
                                                   | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()

        self.project_creator_dialog.tableWidget.setRowCount(len(self.class_labels))
        for i in range(len(self.class_labels)):
            item = QTableWidgetItem(str(i))
            item.setFlags(item.flags() | ~Qt.ItemIsEditable)
            self.project_creator_dialog.tableWidget.setItem(i, 0, item)
            item = QTableWidgetItem('class {}'.format(i))
            self.project_creator_dialog.tableWidget.setItem(i, 1, item)

        def on_next():
            for j in range(len(self.class_labels)):
                label = self.project_creator_dialog.tableWidget.item(j, 1).text()
                self.class_labels.append(label)
            if self.object_detection_mode:
                self.step_4()
            else:
                self.save_settings()

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next)

    @handle_exceptions
    def step_4(self):
        self.project_creator_dialog = loadUi(join(self.folder, 'step_3_4.ui'))
        self.project_creator_dialog.setWindowFlags(
            self.project_creator_dialog.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint)
        self.project_creator_dialog.show()

        self.project_creator_dialog.tableWidget.setRowCount(len(self.class_labels))
        for i in range(len(self.class_labels)):
            item = QTableWidgetItem(str(i))
            item.setFlags(item.flags() | ~Qt.ItemIsEditable)
            self.project_creator_dialog.tableWidget.setItem(i, 0, item)
            item = QTableWidgetItem('object {}'.format(i))
            self.project_creator_dialog.tableWidget.setItem(i, 1, item)

        def on_next():
            for j in range(len(self.object_names)):
                obj = self.project_creator_dialog.tableWidget.item(j, 1).text()
                self.object_names.append(obj)
            self.save_settings()

        self.project_creator_dialog.button_cancel.clicked.connect(self.project_creator_dialog.close)
        self.project_creator_dialog.button_next.clicked.connect(on_next)

    @handle_exceptions
    def save_settings(self):
        self.project_creator_dialog = None

        settings = {'project_name': self.project_name,
                    'author': self.author,
                    'institution': self.institution,
                    'data_folder': self.data_folder,
                    'class_labels': self.class_labels,
                    'object_detection': self.object_detection_mode,
                    'object_names': self.object_names,
                    'last_image': self.img_idx,
                    'copy_images': self.copy_files,
                    'eval_cc': self.eval_cc,
                    'eval_mlo': self.eval_mlo,
                    'eval_mammo': self.eval_mammo,
                    'eval_tomo': self.eval_tomo,
                    'file_extension': self.file_extension}
        path = join(self.project_folder, 'settings.json')

        with open(path, 'w') as json_file:
            json.dump(settings, json_file)



