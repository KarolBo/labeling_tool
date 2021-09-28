from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from main_window import handle_exceptions
from enum import Enum
import numpy as np
import mahotas
import matplotlib.pyplot as plt



class Mode(Enum):
    nothing = 0
    point = 1
    roi = 2
    polygon = 3


class MplWidget(QWidget):

    @handle_exceptions
    def __init__(self, parent=None):

        super().__init__(parent)

        self.canvas = FigureCanvas(Figure())
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        # self.canvas.axes.set_facecolor("red")
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
        self.polygon_x = None
        self.polygon_y = None
        self.polygon = []
        self.mode = Mode.nothing

        self.red_point = None

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
        if new_mode == Mode.nothing or new_mode == Mode.point:
            self.rs = None
            self.location = None
        elif new_mode == Mode.roi:
            self.rs = RectangleSelector(self.canvas.axes, self.roi_select,
                                        drawtype='box', useblit=True, button=[1],
                                        minspanx=5, minspany=5, spancoords='pixels', interactive=True)
        elif new_mode == Mode.polygon:
            self.polygon_x = []
            self.polygon_y = []

        self.mode = new_mode

    @handle_exceptions
    def roi_select(self, click, release):
        x1, y1 = click.xdata, click.ydata
        x2, y2 = release.xdata, release.ydata
        # w = abs(x1 - x2) / self.data_array.shape[1]
        # h = abs(y1 - y2) / self.data_array.shape[0]
        # x = min(x1, x2) / self.data_array.shape[1] + w / 2
        # y = min(y1, y2) / self.data_array.shape[0] + h / 2
        xmin = min(x1, x2) / self.data_array.shape[1]
        xmax = max(x1, x2) / self.data_array.shape[1]
        ymin = min(y1, y2) / self.data_array.shape[0]
        ymax = max(y1, y2) / self.data_array.shape[0]
        self.location = (xmin, xmax, ymin, ymax)

    @handle_exceptions
    def mouse_move(self, event):
        button_number = event.button if type(event.button) is int else event.button.value
        if (button_number == 2 and
                event.xdata is not None and
                event.ydata is not None):
            sensitivity = 2.5
            x = event.xdata
            y = event.ydata
            dx = x - self.x
            dy = y - self.y
            new_min = self.val_min + sensitivity * dx
            new_max = self.val_max + sensitivity * dy
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
        if event.xdata is not None and event.ydata is not None:
            self.x = event.xdata
            self.y = event.ydata
            button_number = event.button if type(event.button) is int else event.button.value
            if button_number == 1:
                if self.mode == Mode.point:
                    x = self.x / self.data_array.shape[1]
                    y = self.y / self.data_array.shape[0]
                    self.location = (x, y)
                    self.draw_point('red') 
                elif self.mode == Mode.polygon:
                    self.polygon_x.append(int(self.x))
                    self.polygon_y.append(int(self.y))
                    self.draw_point('cyan', size=5)

    def draw_point(self, color, size=8):
        if self.location is None and self.polygon_x is None:
            return
        point = self.canvas.axes.scatter(self.x, self.y, c=color, s=size)
        if self.red_point is not None:
            self.red_point.remove()
            self.red_point = None
        if color == 'red':
            self.red_point = point
        if color == 'cyan':
            self.polygon.append(point)
        self.canvas.draw()

    def draw_rect(self):
        if len(self.location) < 4:
            return
        self.canvas.axes.axvspan(xmin=self.location[0] * self.data_array.shape[1],
                                 xmax=self.location[1] * self.data_array.shape[1],
                                 ymin=1-self.location[2],
                                 ymax=1-self.location[3],
                                 facecolor='g', alpha=0.5)
        self.canvas.draw()

    @handle_exceptions
    def draw_polygon(self):
        self.canvas.axes.fill(self.polygon_x, self.polygon_y, c='cyan')
        self.canvas.draw()
        region = self.get_points_inside(self.polygon_x, self.polygon_y)
        self.polygon_x = []
        self.polygon_y = []
        return region

                   
    def reset_polygon(self):
        for a in self.polygon:
            a.remove()
        self.polygon = []
        self.polygon_x = []
        self.polygon_y = []
        self.canvas.draw()


    @handle_exceptions
    def get_points_inside(self, xs, ys):
        poly = list(zip(xs, ys))
        grid = np.zeros((self.data_array.shape[1], self.data_array.shape[0]), dtype=np.int8)
        mahotas.polygon.fill_polygon(poly, grid)
        indices = np.where(grid > 0)
        indices = list(zip(indices[0].tolist(), indices[1].tolist()))
        return indices