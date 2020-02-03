from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Circle
from main_window import handle_exceptions
from enum import Enum


class Mode(Enum):
    window = 1
    point = 2
    roi = 3


class MplWidget(QWidget):

    @handle_exceptions
    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.canvas = FigureCanvas(Figure())
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.axis('off')
        self.setLayout(vertical_layout)

        self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.canvas.mpl_connect('button_press_event', self.mouse_press)
        self.canvas.setMouseTracking(False)

        self.x = None
        self.y = None
        self.val_min = None
        self.val_max = None
        self.data_array = None

        self.rs = None
        self.location = None
        self.mode = Mode.window

    @handle_exceptions
    def display(self):
        self.canvas.axes.clear()
        self.canvas.axes.imshow(self.data_array, cmap='gray',
                                vmin=self.val_min, vmax=self.val_max)
        self.canvas.axes.axis('off')
        self.canvas.draw()

    @handle_exceptions
    def set_mode(self, n):
        new_mode = Mode(n)
        if new_mode == Mode.window or new_mode == Mode.point:
            self.rs = None
            self.location = None
        elif new_mode == Mode.roi:
            self.rs = RectangleSelector(self.canvas.axes, self.roi_select,
                                        drawtype='box', useblit=False, button=[1],
                                        minspanx=5, minspany=5, spancoords='pixels', interactive=True)
        self.mode = new_mode

    @handle_exceptions
    def roi_select(self, click, release):
        x1, y1 = click.xdata, click.ydata
        x2, y2 = release.xdata, release.ydata
        w = abs(x1 - x2) / self.data_array.shape[1]
        h = abs(y1 - y2) / self.data_array.shape[0]
        x = min(x1, x2) / self.data_array.shape[1] + w / 2
        y = min(y1, y2) / self.data_array.shape[0] + h / 2
        self.location = (x, y, w, h)

    @handle_exceptions
    def mouse_move(self, event):
        if self.mode == Mode.window:
            sens = 2.5
            x = event.xdata
            y = event.ydata
            dx = x - self.x
            dy = y - self.y
            new_min = self.val_min + sens * dx
            new_max = self.val_max + sens * dy
            if new_min < new_max:
                if new_min >= self.data_array.min():
                    self.val_min = new_min
                if new_max <= self.data_array.max():
                    self.val_max = new_max
                self.display()
            self.x = x
            self.y = y

    @handle_exceptions
    def mouse_press(self, event):
        self.x = event.xdata
        self.y = event.ydata
        if self.mode == Mode.point:
            x = self.x / self.data_array.shape[1]
            y = self.y / self.data_array.shape[0]
            self.location = (x, y)
            self.display()
            self.canvas.axes.scatter(self.x, self.y)
            self.canvas.draw()