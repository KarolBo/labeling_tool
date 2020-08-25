from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QHeaderView, QActionGroup, \
    QPushButton
from PyQt5.QtGui import QPixmap, QIntValidator
from PyQt5.uic import loadUi
from glob import glob
from os.path import join, isdir, basename, isfile, abspath, exists
from os import mkdir, remove
import sys
from PyQt5.QtCore import pyqtSlot, Qt
import pydicom
from shutil import copyfile
import threading
from scipy.misc import imread
from tutorial import Tutorial
from settings import Settings, handle_exceptions
import subprocess


class MainWindow(QMainWindow):

    @handle_exceptions
    def __init__(self):
        super().__init__()

        self.folder = getattr(sys, '_MEIPASS', abspath('.'))
        loadUi(join(self.folder, 'main_window.ui'), self)

        self.settings = None
        self.image_list = []
        self.result_string = ''
        self.classified = False
        self.objects_located = False
        self.locations = []
        self.object_idx = 0

        self.init_gui()
        self.connect_signals()

        self.start_dialog = None
        self.show_start_dialog()

    @handle_exceptions
    def show_start_dialog(self):
        self.start_dialog = loadUi(join(self.folder, 'start_dialog.ui'))
        self.start_dialog.setWindowFlags(self.start_dialog.windowFlags() | Qt.FramelessWindowHint
                                         | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.start_dialog.button_new.clicked.connect(self.new_project)
        self.start_dialog.button_continue.clicked.connect(self.continue_project)
        self.start_dialog.show()

    @handle_exceptions
    def init_gui(self):
        self.menuBar().setNativeMenuBar(False)
        self.setWindowTitle("The Most Awesome Labelling Tool in the World!")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.line_image_idx.setValidator(QIntValidator(0, 99999, self))

        extension_group = QActionGroup(self)
        extension_group.addAction(self.actionDICOM)
        extension_group.addAction(self.actionPNG)
        self.actionDICOM.setChecked(True)

        logo = QPixmap(join(self.folder, "logo_b_rayZ.png"))
        self.label_logo.setPixmap(logo)

    @handle_exceptions
    def connect_signals(self):
        self.action_copy.triggered.connect(self.create_folders)

        self.button_save_roi.clicked.connect(self.add_location)
        self.button_skip.clicked.connect(self.display_next)
        self.button_skip_step.clicked.connect(self.skip_step)
        self.button_back.clicked.connect(self.get_back)

        self.button_jump.clicked.connect(self.jump_to_img)

        self.button_finish_location.clicked.connect(self.finish_location)

    @pyqtSlot()
    @handle_exceptions
    def new_project(self):
        Tutorial(self)

    @pyqtSlot()
    @handle_exceptions
    def continue_project(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        project_folder = str(file_dialog.getExistingDirectory(self))
        path = join(project_folder, 'settings.json')
        if exists(path):
            settings = Settings()
            settings.load(path)
            self.start_project(settings)

    @handle_exceptions
    def load_data(self):
        pattern = join('**', '*.' + self.settings.file_extension)
        path = join(self.settings.data_folder, pattern)
        self.image_list = glob(path, recursive=True)

    @handle_exceptions
    def filter_forward(self):
        if self.settings.eval_cc and self.settings.eval_mlo and self.settings.eval_mammo and self.settings.eval_tomo:
            return

        to_skip = True
        self.settings.img_idx -= 1
        while (to_skip):
            self.settings.img_idx += 1
            filename = self.image_list[self.settings.img_idx]
            dcm = pydicom.read_file(filename)
            try:
                projection = dcm.ViewPosition
            except:
                projection = "cc mlo"
            try:
                study_description = dcm.StudyDescription
            except:
                study_description = "mammo"
            is_tomo = True if "recon" in study_description.lower() else False
            mlo = 'mlo' in projection.lower()
            cc = 'cc' in projection.lower()
            if ((self.settings.eval_mlo and mlo) or (self.settings.eval_cc and cc)) and \
                    ((self.settings.eval_mammo and not is_tomo) or (self.settings.eval_tomo and is_tomo)):
                to_skip = False

    @handle_exceptions
    def filter_backward(self):
        if self.settings.eval_cc and self.settings.eval_mlo and self.settings.eval_mammo and self.settings.eval_tomo:
            return

        to_skip = True
        self.settings.img_idx += 1
        while (to_skip):
            self.settings.img_idx -= 1
            filename = self.image_list[self.settings.img_idx]
            dcm = pydicom.read_file(filename)
            try:
                projection = dcm.ViewPosition
            except:
                projection = "cc mlo"
            try:
                study_description = dcm.StudyDescription
            except:
                study_description = "mammo"
            is_tomo = True if "recon" in study_description.lower() else False
            mlo = 'mlo' in projection.lower()
            cc = 'cc' in projection.lower()
            if ((self.settings.eval_mlo and mlo) or (self.settings.eval_cc and cc)) and \
                    ((self.settings.eval_mammo and not is_tomo) or (self.settings.eval_tomo and is_tomo)):
                to_skip = False

    @handle_exceptions
    def start_project(self, settings):
        del self.start_dialog
        self.start_dialog = None
        self.settings = settings
        self.load_data()
        self.show()
        self.screen.set_mode(self.settings.object_detection_mode)
        self.reset_state()
        if self.settings.copy_files:
            self.create_folders()
        self.create_result_file()
        self.create_buttons()
        if self.settings.class_labels:
            self.fill_class_table()
        self.button_save_roi.setEnabled(self.settings.object_detection_mode)
        self.button_finish_location.setEnabled(self.settings.object_detection_mode)
        self.display_hint()
        self.display()

    @pyqtSlot()
    @handle_exceptions
    def create_folders(self):
        if self.settings.copy_files:
            n = len(self.settings.class_labels)
            for i in range(n):
                folder_name = join(self.settings.project_folder, self.settings.class_labels[i])
                if not isdir(folder_name):
                    mkdir(folder_name)

    @handle_exceptions
    def create_buttons(self):
        n = len(self.settings.class_labels)
        stylesheet = """background: #ff655a;
                        font: inherit;
                        border: 1px solid grey;
                        border-radius: 6px;
                        adding: 0.25rem 1rem;
                        margin-right: 1rem;
                        color: white;
                        height: 40px;
                        font-size: 20;"""
        for i in reversed(range(self.buttons_layout.count())):
            self.buttons_layout.itemAt(i).widget().setParent(None)
        for i in range(n):
            button = QPushButton(self.settings.class_labels[i])
            button.setStyleSheet(stylesheet)
            button.clicked.connect(lambda event, cls=i: self.classify(cls))
            self.buttons_layout.addWidget(button)

    @handle_exceptions
    def fill_class_table(self):
        n = len(self.settings.class_labels)
        self.table.setRowCount(n)
        for i in range(n):
            item = QTableWidgetItem(self.settings.class_labels[i])
            self.table.setItem(i, 0, item)
        labels = [str(i) for i in range(n)]
        self.table.setVerticalHeaderLabels(labels)

    @pyqtSlot()
    @handle_exceptions
    def display(self):
        self.filter_forward()
        if self.settings.file_extension == 'dcm':
            dcm_file_name = self.image_list[self.settings.img_idx]
            subprocess.call(("dcmdjpeg", dcm_file_name, dcm_file_name))
            dcm_file = pydicom.dcmread(dcm_file_name)
            self.screen.val_min, self.screen.val_max = self.get_windowing(dcm_file)
            self.screen.data_array = dcm_file.pixel_array
        else:
            self.screen.data_array = imread(self.image_list[self.settings.img_idx])
        self.screen.display()

        self.line_image_idx.setText(str(self.settings.img_idx + 1))
        self.label_total_images.setText(' / ' + str(len(self.image_list)))

    @handle_exceptions
    def reset_state(self):
        self.result_string = ''
        self.classified = False
        if self.settings.object_detection_mode:
            self.set_buttons_enabled(False)
            self.object_idx = 0
            self.locations = len(self.settings.object_names) * [False]

        self.checkbox_implants.setChecked(False)
        self.checkbox_reduction.setChecked(False)
        self.checkbox_surgery.setChecked(False)
        self.checkbox_other.setChecked(False)

        self.objects_located = False

    @pyqtSlot()
    @handle_exceptions
    def display_next(self):
        self.settings.img_idx += 1
        self.reset_state()
        if self.settings.img_idx < len(self.image_list):
            self.display_hint()
            self.display()
        else:
            self.finito()

    @pyqtSlot()
    @handle_exceptions
    def jump_to_img(self):
        self.reset_state()
        self.settings.img_idx = int(self.line_image_idx.text()) - 1
        self.display()
        self.display_hint()

    @pyqtSlot()
    @handle_exceptions
    def get_back(self):
        if self.settings.img_idx < 1:
            return

        self.settings.img_idx -= 1;
        self.filter_backward()
        file_name = basename(self.image_list[self.settings.img_idx])

        # remove file
        if self.settings.copy_files:
            n = len(self.settings.class_labels)
            for i in range(n):
                file_path = join(self.project_folder, self.settings.class_labels[i], file_name)
                if isfile(file_path):
                    remove(file_path)
                    print('Removed {}'.format(file_path))

        # remove location row
        path = join(self.settings.project_folder, self.settings.project_name + '.csv')
        if isfile(path):
            with open(path, "r") as f:
                lines = f.readlines()
            with open(path, "w") as f:
                for line in lines:
                    if file_name not in line:
                        f.write(line)

        # display previous image
        self.display()
        self.display_hint()

    @pyqtSlot()
    @handle_exceptions
    def skip_step(self):
        if self.settings.object_detection_mode and (self.object_idx < len(self.settings.object_names)):
            self.screen.location = "None, None"
            self.screen.x = None
            self.screen.y = None
            self.add_location()
        elif len(self.settings.class_labels):
            self.classify(None)

    @handle_exceptions
    def set_buttons_enabled(self, state):
        n = self.buttons_layout.count()
        for i in range(n):
            b = self.buttons_layout.itemAt(i).widget()
            b.setEnabled(state)

    @handle_exceptions
    def get_windowing(self, dcm_file):
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
    def classify(self, class_nr):
        if self.settings.img_idx <= len(self.image_list):
            print('you classified as:', class_nr)
            self.result_string += ',' + str(class_nr)
            if self.settings.copy_files:
                src_path = self.image_list[self.settings.img_idx]
                target_path = join(self.project_folder, self.settings.class_labels[class_nr], basename(src_path))
                self.copy(src_path, target_path)
            self.classified = True
            if self.is_ready():
                self.save_result()
                self.display_next()

    @pyqtSlot()
    @handle_exceptions
    def add_location(self):
        if (self.settings.object_names and
                self.object_idx >= len(self.settings.object_names)):
            return

        if self.settings.object_names:
            self.locations[self.object_idx] = True
            self.object_idx += 1

        if self.settings.object_detection_mode == 1:
            self.screen.draw_point('lawngreen')
        elif self.settings.object_detection_mode == 2:
            self.screen.draw_rect()
        self.result_string += ',' + str(self.screen.location).strip('()')
        if self.is_ready():
            self.save_result()
            self.display_next()
        elif self.objects_located or \
                (self.settings.class_labels is not None and self.object_idx == len(self.settings.object_names)):
            self.set_buttons_enabled(True)

    @pyqtSlot()
    @handle_exceptions
    def finish_location(self):
        self.objects_located = True

    @handle_exceptions
    def create_result_file(self):
        path = join(self.settings.project_folder, self.settings.project_name + '.csv')
        if isfile(path):
            return
        with open(path, 'w') as file:
            headers = 'file'
            if self.settings.object_detection_mode == 1:
                for obj in self.settings.object_names:
                    headers += ',' + obj + ' x'
                    headers += ',' + obj + ' y'
            elif self.settings.object_detection_mode == 2:
                for obj in self.settings.object_names:
                    headers += ',' + obj + ' x1'
                    headers += ',' + obj + ' x2'
                    headers += ',' + obj + ' y2'
                    headers += ',' + obj + ' y2'
            if self.settings.class_labels:
                headers += ',class'
            headers += ',comments'

            file.write(headers + '\n')

    @handle_exceptions
    def save_result(self):
        if self.settings.img_idx > len(self.image_list):
            return
        path = join(self.settings.project_folder, self.settings.project_name + '.csv')
        if self.checkbox_implants.isChecked():
            self.result_string += ',implant'
        if self.checkbox_reduction.isChecked():
            self.result_string += ',reduction'
        if self.checkbox_surgery.isChecked():
            self.result_string += ',surgery'
        if self.checkbox_other.isChecked():
            self.result_string += ',other'

        with open(path, 'a+') as file:
            filename = basename(self.image_list[self.settings.img_idx])
            file.write(filename + self.result_string + '\n')

    @handle_exceptions
    def is_ready(self):
        self.display_hint()

        class_checked = (len(self.settings.class_labels) > 0)
        object_checked = (self.settings.object_detection_mode > 0)
        if self.settings.object_names:
            self.objects_located = (self.object_idx == len(self.settings.object_names))
        status = (self.classified or not class_checked) and (self.objects_located or not object_checked)

        return status

    @handle_exceptions
    def copy(self, src_path, target_path):
        process_thread = threading.Thread(target=copyfile, args=(src_path, target_path))
        process_thread.daemon = True
        process_thread.start()

    @handle_exceptions
    def keyPressEvent(self, event):
        # print(event.key())
        class_checked = (self.settings.class_labels is not None)
        object_checked = self.settings.object_detection_mode
        if event.key() == 116777219:
            self.get_back()
        elif event.key() == 16777220 and object_checked:
            self.add_location()
        elif event.key() == 16777234:
            if class_checked:
                self.classify(0)
        elif event.key() == 16777236:
            if class_checked:
                self.classify(1)
        elif event.key() == 16777216:
            self.closeEvent(None)
        else:
            class_num = event.key() - 48
            if class_checked and class_num < len(self.settings.class_labels):
                self.classify(class_num)
        event.accept()

    @handle_exceptions
    def display_hint(self):
        if self.settings.object_detection_mode > 0 and (self.object_idx < len(self.settings.object_names)):
            self.hint_label.setText('Mark the {}'.format(self.settings.object_names[self.object_idx]))
        elif self.settings.object_detection_mode > 0 and \
                len(self.settings.object_names) == 0 and not \
                self.objects_located:
            self.hint_label.setText('Mark next object')
        elif len(self.settings.class_labels):
            self.hint_label.setText('Choose the class')

    @handle_exceptions
    def finito(self):
        self.screen.canvas.axes.clear()
        self.screen.canvas.draw()
        self.set_buttons_enabled(False)
        self.table.setEnabled(False)
        self.button_save_roi.setEnabled(False)

    @handle_exceptions
    def closeEvent(self, event):
        if self.settings.data_folder:
            self.settings.save()
        self.close()


##########################################################################################


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
