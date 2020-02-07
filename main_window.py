from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QHeaderView
from PyQt5.QtGui import QIntValidator
from PyQt5.uic import loadUi
from glob import glob
from os.path import join, isdir, basename, isfile, abspath
from os import mkdir, remove
import sys
from PyQt5.QtCore import pyqtSlot
import pydicom
from shutil import copyfile
import functools


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


class MainWindow(QMainWindow):

    @handle_exceptions
    def __init__(self):
        super().__init__()

        folder = getattr(sys, '_MEIPASS', abspath('.'))
        loadUi(join(folder, 'main_window.ui'), self)

        self.menuBar().setNativeMenuBar(False)
        self.setWindowTitle("The Most Awesome Labelling Tool in the World!")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.num_of_classes.setValidator(QIntValidator(0, 100, self))

        self.image_list = ''
        self.target_folder = ''
        self.file_extension = 'dcm'
        self.img_idx = -1
        self.classified = False
        self.located = False

        self.connect_signals()

    @handle_exceptions
    def connect_signals(self):
        self.menu_open.triggered.connect(self.load_folder)
        self.menu_save.triggered.connect(self.set_target_folder)
        self.button_confirm.clicked.connect(self.set_categories)
        self.checkbox_class.stateChanged.connect(self.on_checkbox)
        self.checkbox_object.stateChanged.connect(self.on_checkbox)
        self.box.clicked.connect(self.on_toggle)
        self.point.clicked.connect(self.on_toggle)
        self.button_save_roi.clicked.connect(self.save_location)
        self.button_skip.clicked.connect(self.display_next)
        self.button_back.clicked.connect(self.get_back)

    @pyqtSlot()
    @handle_exceptions
    def display_next(self):
        if self.img_idx < len(self.image_list)-1:
            self.img_idx += 1
            dcm_file = pydicom.dcmread(self.image_list[self.img_idx])
            self.screen.data_array = dcm_file.pixel_array
            self.screen.val_min, self.screen.val_max = self.get_window(dcm_file)
            self.screen.display()
            self.label_image_num.setText(str(self.img_idx+1) + ' / ' + str(len(self.image_list)))
            self.located = self.classified = False
            self.on_toggle()
            if self.checkbox_object.isChecked():
                self.set_buttons_enabled(False)
        else:
            self.finito()

    @handle_exceptions
    def set_buttons_enabled(self, state):
        n = self.buttons_layout.count()
        for i in range(n):
            b = self.buttons_layout.itemAt(i).widget()
            b.setEnabled(state)

    @handle_exceptions
    def get_window(self, dcm_file):
        if "WindowCenter" in dcm_file and "WindowWidth" in dcm_file:
            center = dcm_file.WindowCenter
            width = dcm_file.WindowWidth
            if isinstance(center, pydicom.multival.MultiValue):
                center = center[0]
                width = width[0]
            val_min = center - 0.5 * width
            val_max = center + 0.5 * width
        else:
            val_min = None
            val_max = None
        return val_min, val_max

    @pyqtSlot()
    @handle_exceptions
    def load_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        source_folder = str(file_dialog.getExistingDirectory(self))
        if not self.target_folder:
            self.target_folder = source_folder
        path = join(source_folder, '*.'+self.file_extension)
        self.image_list = glob(path)
        self.display_next()
        self.restore_work()

    @pyqtSlot()
    @handle_exceptions
    def set_target_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.target_folder = str(file_dialog.getExistingDirectory(self))
        print('target folder:', self.target_folder)
        if self.image_list:
            self.restore_work()

    @handle_exceptions
    def classify(self, class_nr):
        if self.img_idx < len(self.image_list):
            print('you classified as:', class_nr)
            src_path = self.image_list[self.img_idx]
            target_path = join(self.target_folder, str(class_nr), basename(src_path))
            copyfile(src_path, target_path)
            self.classified = True
            if self.is_ready():
                self.display_next()
        else:
            self.finito()

    @pyqtSlot()
    @handle_exceptions
    def set_categories(self):
        if self.num_of_classes.text():
            n = int(self.num_of_classes.text())
        else:
            n = 0
        self.create_buttons(n)
        self.create_folders(n)
        self.add_rows(n)

    @handle_exceptions
    def create_buttons(self, n):
        for i in reversed(range(self.buttons_layout.count())):
            self.buttons_layout.itemAt(i).widget().setParent(None)
        for i in range(n):
            button = QPushButton("class "+str(i))
            button.clicked.connect(lambda event, cls=i: self.classify(cls))
            self.buttons_layout.addWidget(button)

    @handle_exceptions
    def create_folders(self, n):
        for i in range(n):
            folder_name = join(self.target_folder, str(i))
            if not isdir(folder_name):
                mkdir(folder_name)

    @handle_exceptions
    def add_rows(self, n):
        self.table.setRowCount(0)
        for i in range(n):
            self.table.insertRow(self.table.rowCount())
        self.table.setFocusPolicy(False)

    @handle_exceptions
    def restore_work(self, n=99):
        labeled_imgs = set()
        class_number = 0
        for i in range(n):
            folder_name = join(self.target_folder, str(i))
            if isdir(folder_name):
                file_list = glob(join(folder_name,'*'))
                file_list = [basename(path) for path in file_list]
                labeled_imgs.update(file_list)
                class_number = i + 1

        path = join(self.target_folder, 'locations.csv')
        if isfile(path):
            self.checkbox_object.setChecked(True)
            with open(path, "r") as f:
                lines = f.readlines()
            file_list = [file_name.split(',')[0] for file_name in lines]
            labeled_imgs.update(file_list)

        for file in self.image_list:
            if basename(file) in labeled_imgs:
                self.img_idx += 1

        if self.img_idx:
            self.img_idx -= 1
            self.display_next()

        if class_number:
            self.checkbox_class.setChecked(True)
            self.num_of_classes.setText(str(class_number))
            self.set_categories()

    @handle_exceptions
    def keyPressEvent(self, event):
        # print(event.key())
        if event.key() == 116777219:
            self.get_back()
        elif event.key() == 16777220 and self.checkbox_object.isChecked():
            self.save_location()
        else:
            class_num = event.key() - 48
            if self.num_of_classes.text() and class_num < int(self.num_of_classes.text()):
                self.classify(class_num)
        event.accept()

    @pyqtSlot()
    @handle_exceptions
    def on_checkbox(self):
        class_checked = self.checkbox_class.isChecked()
        object_checked = self.checkbox_object.isChecked()
        box_checked = self.box.isChecked()

        self.label.setEnabled(class_checked)
        self.num_of_classes.setEnabled(class_checked)
        self.button_confirm.setEnabled(class_checked)
        self.table.setEnabled(class_checked)

        self.point.setEnabled(object_checked)
        self.box.setEnabled(object_checked)

        state = class_checked and (not object_checked or (object_checked and self.located))
        self.set_buttons_enabled(state)

        if not object_checked:
            self.screen.set_mode(0)
        else:
            if box_checked:
                self.screen.set_mode(2)
            else:
                self.screen.set_mode(1)

    @pyqtSlot()
    @handle_exceptions
    def on_toggle(self):
        self.screen.display()
        object_checked = self.checkbox_object.isChecked()
        box_checked = self.box.isChecked()
        if object_checked:
            if box_checked:
                self.screen.set_mode(2)
            else:
                self.screen.set_mode(1)

    @pyqtSlot()
    @handle_exceptions
    def save_location(self):
        if self.img_idx < len(self.image_list):
            path = join(self.target_folder, 'locations.csv')
            with open(path, 'a+') as file:
                filename = basename(self.image_list[self.img_idx])
                location = str(self.screen.location).strip('()')
                file.write(filename+','+location+'\n')
            self.located = True
            self.screen.draw_point('lawngreen')
            if self.is_ready():
                self.display_next()
            elif self.checkbox_class.isChecked():
                self.set_buttons_enabled(True)
        else:
            self.finito()

    @handle_exceptions
    def finito(self):
        self.screen.canvas.axes.clear()
        self.screen.canvas.draw()
        self.set_buttons_enabled(False)
        self.label.setEnabled(False)
        self.table.setEnabled(False)
        self.point.setEnabled(False)
        self.box.setEnabled(False)
        self.button_save_roi.setEnabled(False)

    @handle_exceptions
    def revive(self):
        class_checked = self.checkbox_class.isChecked()
        object_checked = self.checkbox_object.isChecked()
        self.set_buttons_enabled(class_checked)
        self.label.setEnabled(class_checked)
        self.table.setEnabled(class_checked)
        self.point.setEnabled(object_checked)
        self.box.setEnabled(object_checked)
        self.button_save_roi.setEnabled(object_checked)

    @handle_exceptions
    def is_ready(self):
        class_checked = self.checkbox_class.isChecked()
        object_checked = self.checkbox_object.isChecked()

        status = (self.classified or not class_checked) and (self.located or not object_checked)
        return status

    @pyqtSlot()
    @handle_exceptions
    def get_back(self):
        if self.num_of_classes.text():
            n = int(self.num_of_classes.text())
        else:
            n = 0
        file_name = basename(self.image_list[self.img_idx-1])

        # remove file
        for i in range(n):
            file_path = join(self.target_folder, str(i), file_name)
            if isfile(file_path):
                remove(file_path)
                print('Removed {}'.format(file_path))

        # remove location row
        path = join(self.target_folder, 'locations.csv')
        if isfile(path):
            with open(path, "r") as f:
                lines = f.readlines()
            with open(path, "w") as f:
                for line in lines:
                    if file_name not in line:
                        f.write(line)

        # display previous image
        if self.img_idx > 0:
            self.img_idx -= 2
            self.display_next()

        self.revive()


##########################################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    app.exec_()
