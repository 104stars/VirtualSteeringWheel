import sys
import os
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QTransform

class TransparentWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initPygame()
        self.offset = None

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        
        self.label = QLabel(self)
        
        # Determine the correct path to the image
        if getattr(sys, 'frozen', False):  # PyInstaller bundle
            base_path = sys._MEIPASS
        else:  # Running in IDE
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        image_path = os.path.join(base_path, "steering_wheel.png")
        self.pixmap = QPixmap(image_path)
        self.original_pixmap = self.pixmap
        self.label.setPixmap(self.pixmap)
        self.resize(self.pixmap.width(), self.pixmap.height())
        
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, screen.height() - self.height() //2)

    def initPygame(self):
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("No joysticks found!")
            self.close()
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wheel)
        self.timer.start(16)  # ~60 FPS

    def update_wheel(self):
        pygame.event.pump()
        x_axis = self.joystick.get_axis(0)
        angle = x_axis * 270  # Invert the angle calculation

        transform = QTransform().rotate(angle)  # Apply the inverted angle
        rotated_pixmap = self.resized_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        self.label.setPixmap(rotated_pixmap)
        self.label.setGeometry(
            (self.width() - rotated_pixmap.width()) // 2,
            (self.height() - rotated_pixmap.height()) // 2,
            rotated_pixmap.width(),
            rotated_pixmap.height()
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            sys.exit()  # Terminate the process

    def setDimensions(self, size):
        self.resize(size, size)
        self.resized_pixmap = self.original_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.update_wheel()  # Update the wheel size to fit the new dimensions

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TransparentWindow()
    ex.show()
    ex.setDimensions(180)  # Example to programmatically set the dimensions
    sys.exit(app.exec_())
