from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton
from PyQt5.uic import loadUi
from glob import glob
from os.path import join, isdir, basename
from os import mkdir
from PyQt5.QtCore import pyqtSlot, Qt
import pydicom
from shutil import copyfile


def handle_exceptions(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            return None
    return func_wrapper


class MainWindow(QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("main_window.ui",self)
        self.menuBar().setNativeMenuBar(False)
        self.setWindowTitle("The Most Awesome Labelling Tool in the World!")

        self.image_list = ''
        self.target_folder = ''
        self.file_extension = 'dcm'
        self.img_idx = 0

        self.connect_signals()

    def connect_signals(self):
        self.menu_open.triggered.connect(self.load_folder)
        self.menu_save.triggered.connect(self.set_target_folder)
        self.button_confirm.clicked.connect(self.set_categories)

    @handle_exceptions
    def display(self, image):
        self.screen.canvas.axes.clear()
        self.screen.canvas.axes.imshow(image, cmap='gray')
        self.screen.canvas.axes.axis('off')
        self.screen.canvas.draw()
        self.label_image_num.setText(str(self.img_idx+1)+' / '+str(len(self.image_list)))

    # @pyqtSlot()
    # @handle_exceptions
    def load_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        source_folder = str(file_dialog.getExistingDirectory(self))
        path = join(source_folder, '*.'+self.file_extension)
        self.image_list = glob(path)
        self.display_next()

    # @pyqtSlot()
    # @handle_exceptions
    def set_target_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        self.target_folder = str(file_dialog.getExistingDirectory(self))
        self.img_idx += 0
        print('target folder:', self.target_folder)

    @handle_exceptions
    def display_next(self):
        if self.image_list:
            dcm_file = pydicom.dcmread(self.image_list[self.img_idx])
            data_array = dcm_file.pixel_array
            self.display(data_array)

    @handle_exceptions
    def classify(self, class_nr):
        if self.image_list:
            print('you classified as:', class_nr)
            src_path = self.image_list[self.img_idx]
            target_path = join(self.target_folder, str(class_nr), src_path.split('/')[-1])
            copyfile(src_path, target_path)
            self.img_idx += 1
            self.display_next()

    # @pyqtSlot()
    # @handle_exceptions
    def set_categories(self):
        n = int(self.num_of_classes.text())
        self.create_buttons(n)
        self.create_folders(n)
        self.check_folders(n)

    @handle_exceptions
    def create_buttons(self, n):
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
    def check_folders(self, n):
        labeled_imgs = set()
        for i in range(n):
            folder_name = join(self.target_folder, str(i))
            file_list = glob(join(folder_name,'*'))
            file_list = [basename(path) for path in file_list]
            labeled_imgs.update(file_list)

        for file in self.image_list:
            if basename(file) in labeled_imgs:
                self.img_idx += 1

        if self.img_idx:
            self.display_next()

    def keyPressEvent(self, event):
        class_num = event.key() - 48
        if class_num < int(self.num_of_classes.text()):
            self.classify(class_num)
        event.accept()



##########################################################################################

app = QApplication([])
window = MainWindow()
window.showFullScreen()
app.exec_()
