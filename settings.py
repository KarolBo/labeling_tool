import json
import functools
from os.path import join, exists


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


class Settings:

    @handle_exceptions
    def __init__(self):
        self.project_name = ''
        self.author = ''
        self.institution = ''
        self.project_folder = ''
        self.data_folder = ''
        self.class_labels = []
        self.classification_mode = 0  # 0 - none, 1 - class per image, 2 - class per location
        self.object_detection_mode = 0  # 0 - none, 1 - point, 2 - square, 3 - polygon
        self.object_names = []
        self.img_idx = 0
        self.eval_cc = self.eval_mlo = self.eval_mammo = self.eval_tomo = True
        self.copy_files = False
        self.file_extension = 'dcm'
        self.decode = False

    @handle_exceptions
    def save(self):
        settings_dict = {'project_name': self.project_name,
                         'author': self.author,
                         'institution': self.institution,
                         'data_folder': self.data_folder,
                         'project_folder': self.project_folder,
                         'class_labels': self.class_labels,
                         'classification_mode': self.classification_mode,
                         'object_detection': self.object_detection_mode,
                         'object_names': self.object_names,
                         'last_image': self.img_idx,
                         'copy_images': self.copy_files,
                         'eval_cc': self.eval_cc,
                         'eval_mlo': self.eval_mlo,
                         'eval_mammo': self.eval_mammo,
                         'eval_tomo': self.eval_tomo,
                         'file_extension': self.file_extension,
                         'decode': self.decode,
                         'copy_files': self.copy_files}
        path = join(self.project_folder, 'settings.json')

        with open(path, 'w') as json_file:
            json.dump(settings_dict, json_file)

    @handle_exceptions
    def load(self, path):
        if exists(path):
            with open(path, 'r') as json_file:
                settings_dict = json.load(json_file)

            self.project_name = settings_dict['project_name']
            self.author = settings_dict['author']
            self.institution = settings_dict['institution']
            self.img_idx = settings_dict['last_image']
            self.data_folder = settings_dict['data_folder']
            self.class_labels = settings_dict['class_labels']
            self.object_names = settings_dict['object_names']
            self.classification_mode = settings_dict['classification_mode']
            self.object_detection_mode = settings_dict['object_detection']
            self.copy_files = settings_dict['copy_images']
            self.eval_cc = settings_dict['eval_cc']
            self.eval_mlo = settings_dict['eval_mlo']
            self.eval_mammo = settings_dict['eval_mammo']
            self.eval_tomo = settings_dict['eval_tomo']
            self.project_folder = settings_dict['project_folder']
            self.file_extension = settings_dict['file_extension']
            self.decode = settings_dict['decode']
