import sys, ctypes, os
import pyaudio, audioop, threading
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QIcon, QGuiApplication
from queue import Queue
from math import log10

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.subproduct.version')

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(resource_path("assets/monkey_icon_256.png")))

def svg_as_pixmap(path, height=None):
    renderer = QSvgRenderer(path)
    size = renderer.defaultSize()
    if height:
        size = size.scaled(int(size.width() * height / size.height()), height,
                           Qt.AspectRatioMode.KeepAspectRatio)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap

def add_label(self, pixmap):
    label = QLabel(self)
    label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    label.setPixmap(pixmap)
    return label

# monkey pixmaps
monkey_calm_pixmap = QPixmap(resource_path("assets/monkey_calm.png")).scaled(120, 120)
monkey_annoyed_pixmap = QPixmap(resource_path("assets/monkey_annoyed.png")).scaled(120, 120)
monkey_agitated_pixmap = QPixmap(resource_path("assets/monkey_agitated.png")).scaled(120, 120)
monkey_howling_pixmap = QPixmap(resource_path("assets/monkey_howling.png")).scaled(120, 120)

db_queue = Queue()

def listen():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024)
    while True:
        try:
            data = stream.read(1024)
            rms = audioop.rms(data, 2)
            if rms == 0: rms = 1
            db = 20 * log10(rms)
            db_queue.put(db)
        except Exception as e:
            print(f'\nAudio capture error: {e}')
            break

def update_monkey(db, db_min=0, db_max=90, curve=2.5):
    level = max(0, min(db, db_max) - db_min) / (db_max - db_min)
    level = level ** curve
    if level < 0.3:
        return monkey_calm_pixmap
    elif level < 0.75:
        return monkey_annoyed_pixmap
    elif level < 0.85:
        return monkey_agitated_pixmap
    else:
        return monkey_howling_pixmap

audio_thread = threading.Thread(target=listen, daemon=True)
audio_thread.start()

arc_pixmaps = [
    svg_as_pixmap(resource_path(f'./assets/arc_{i}.svg')) for i in range(1, 15) 
]

def lit_arc_count(db, db_min=0, db_max=90, curve=2.5):
    level = max(0, min(db, db_max) - db_min) / (db_max - db_min)
    level = level ** curve
    return min(int(level * len(arc_pixmaps)), len(arc_pixmaps))

class ClickableLabel(QLabel):
    def __init__(self, pixmap, on_click, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setPixmap(pixmap)
        self.on_click = on_click

    def mousePressEvent(self, event):
        self.on_click()

class OverlayWindow(QWidget):
    def mousePressEvent(self, event):
        self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowIcon(QIcon(resource_path("assets/monkey_icon.ico")))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(320, 150)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width(), screen.bottom() - self.height())

        # SVGs
        left_leaves_pixmap = svg_as_pixmap(resource_path('assets/left_leaves.svg'), height=100)
        self.left_leaves_label = add_label(self, left_leaves_pixmap)
        self.left_leaves_label.setGeometry(0, 150 - left_leaves_pixmap.height(),
                                           left_leaves_pixmap.width(),
                                           left_leaves_pixmap.height())

        right_leaves_pixmap = svg_as_pixmap(resource_path('assets/right_leaves.svg'), height=100)
        self.right_leaves_label = add_label(self, right_leaves_pixmap)
        self.right_leaves_label.setGeometry(320 - right_leaves_pixmap.width(), 150 - right_leaves_pixmap.height(),
                                           right_leaves_pixmap.width(),
                                           right_leaves_pixmap.height())

        mic_pixmap = svg_as_pixmap(resource_path('assets/mic.svg'), height=50)
        self.mic_label = add_label(self, mic_pixmap)
        self.mic_label.setGeometry(25, 50, mic_pixmap.width(), mic_pixmap.height())

        # arcs
        self.arc_labels = []
        for i, pixmap in enumerate(arc_pixmaps):
            label = add_label(self, pixmap)
            x, y = self.arc_position(i, len(arc_pixmaps), pixmap)
            label.setGeometry(x, y, pixmap.width(), pixmap.height())
            label.setVisible(False)
            self.arc_labels.append(label)

        # monkey
        self.monkey_label = add_label(self, monkey_calm_pixmap)
        self.monkey_label.setGeometry(215, 25, 120, 120)
        self.monkey_label.raise_() 

        # buttons
        self.x_label = ClickableLabel(svg_as_pixmap(resource_path('assets/x.svg'), 20), app.quit, parent=self)
        self.x_label.setGeometry(320-22, 5, 22, 22)

        move_pixmap = svg_as_pixmap(resource_path('assets/move.svg'), height=30)
        self.move_label = add_label(self, move_pixmap)
        self.move_label.setGeometry(5, 5, move_pixmap.width(), move_pixmap.height())

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(50)

    def arc_position(self, index, total, pixmap):
        spacing = 175 // (total + 1)
        return spacing * (index + 1) + 60, 80 - pixmap.height() // 2

    def refresh(self):
        latest_db = None
        while not db_queue.empty():
            latest_db = db_queue.get()

        if latest_db is not None:
            self.monkey_label.setPixmap(update_monkey(latest_db))
            count = lit_arc_count(latest_db)
            for i, label in enumerate(self.arc_labels):
                label.setVisible(i < count)

window = OverlayWindow()
window.show()
sys.exit(app.exec())