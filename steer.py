import sys
import os
import pygame
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QSlider, QVBoxLayout, QPushButton, QDialog,
                             QTabWidget, QHBoxLayout, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QTransform, QIntValidator
import json

# Utility to get resource paths for PyInstaller and normal runs
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load persistent settings from settings.json
settings_path = resource_path("settings.json")
try:
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except Exception as e:
    print(f"Error loading settings.json: {e}")
    settings = {}

# List files in the wheels folder
wheels_folder = resource_path("wheels")
if os.path.isdir(wheels_folder):
    wheels_files = os.listdir(wheels_folder)
else:
    print("wheels folder not found!")
    wheels_files = []

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Cache paths to avoid repeated calculations
        self._base_path = resource_path("")
        self._wheels_dir = resource_path("wheels")
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()
        self.visual_tab = QWidget()
        self.wheels_tab = QWidget()

        self.tabs.addTab(self.visual_tab, "Visual")
        self.tabs.addTab(self.wheels_tab, "Wheels")

        self.setup_visual_tab()
        self.setup_wheels_tab()

        layout.addWidget(self.tabs)

        # Add Apply and Save buttons
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.save_button = QPushButton("Save")
        self.apply_button.clicked.connect(self.apply_changes)
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def setup_visual_tab(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Opacity slider
        opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.parent.opacity_value)

        layout.addWidget(opacity_label)
        layout.addWidget(self.opacity_slider)

        dimension_label = QLabel("Window Size (90-360):")
        self.dimension_input = QLineEdit()
        self.dimension_input.setValidator(QIntValidator(90, 360))
        self.dimension_input.setText(str(self.parent.dimension))  # Assuming the window is square

        layout.addWidget(dimension_label)
        layout.addWidget(self.dimension_input)

        layout.addStretch(1)

        self.visual_tab.setLayout(layout)

    def setup_wheels_tab(self):
        layout = QVBoxLayout()

        # Wheel selection
        wheel_label = QLabel("Choose your wheel")
        layout.addWidget(wheel_label)

        wheel_layout = QHBoxLayout()
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.wheel_image = QLabel()
        self.wheel_image.setFixedSize(200, 200)
        self.wheel_counter = QLabel("1/3")  # Placeholder, update with actual count

        wheel_layout.addWidget(self.prev_button)
        wheel_layout.addWidget(self.wheel_image)
        wheel_layout.addWidget(self.next_button)

        layout.addLayout(wheel_layout)
        layout.addWidget(self.wheel_counter, alignment=Qt.AlignCenter)

        self.wheels_tab.setLayout(layout)

        # Load wheels
        self.wheels = self.load_wheels()
        self.current_wheel_index = 0
        self.update_wheel_display()

        # Connect buttons
        self.prev_button.clicked.connect(self.prev_wheel)
        self.next_button.clicked.connect(self.next_wheel)

    def load_wheels(self):
        try:
            return [f for f in os.listdir(self._wheels_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except FileNotFoundError:
            return []

    def update_wheel_display(self):
        if not self.wheels:
            return
            
        current_wheel = self.wheels[self.current_wheel_index]
        wheel_path = os.path.join(self._wheels_dir, current_wheel)
        if os.path.exists(wheel_path):
            pixmap = QPixmap(wheel_path)
            self.wheel_image.setPixmap(pixmap.scaled(
                200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.wheel_counter.setText(f"{self.current_wheel_index + 1}/{len(self.wheels)}")

    def prev_wheel(self):
        if self.wheels:
            self.current_wheel_index = (self.current_wheel_index - 1) % len(self.wheels)
            self.update_wheel_display()

    def next_wheel(self):
        if self.wheels:
            self.current_wheel_index = (self.current_wheel_index + 1) % len(self.wheels)
            self.update_wheel_display()

    def apply_changes(self):
        # Apply opacity changes
        self.parent.opacity_value = self.opacity_slider.value()
        self.parent.update_opacity()

        # Apply dimension changes
        new_dimension = self.dimension_input.text()
        if new_dimension:
            try:
                new_dimension = int(new_dimension)
                if 90 <= new_dimension <= 360:
                    self.parent.setDimensions(new_dimension)
                else:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a value between 90 and 360.")
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

        # Apply wheel changes (if any)
        if self.wheels:
            wheel_path = os.path.join(self._wheels_dir, self.wheels[self.current_wheel_index])
            if os.path.exists(wheel_path):
                self.parent.change_wheel(wheel_path)

    def save_changes(self):
        # Save changes to parent and persist settings
        self.parent.opacity_value = self.opacity_slider.value()
        self.parent.setDimensions(int(self.dimension_input.text()))
        self.parent.save_settings()
        self.accept()

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._base_path = resource_path("")
        self._wheels_dir = resource_path("wheels")
        self.opacity_value = 255
        self.last_angle = 0
        self.offset = None
        self.current_wheel = None
        self.dimension = 180  # Default size
        self.load_settings()  # Load settings BEFORE UI setup
        # Apply settings immediately in initUI
        self.initUI()
        self.initPygame()

    def load_settings(self):
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    data = json.load(f)
                self.opacity_value = data.get("opacity_value", 255)
                self.dimension = data.get("dimension", 180)
                self.current_wheel = data.get("current_wheel", None)
            except Exception as e:
                print(f"Failed to load settings: {e}")
        else:
            self.opacity_value = 255
            self.dimension = 180
            self.current_wheel = None

    def save_settings(self):
        data = {
            "opacity_value": self.opacity_value,
            "dimension": self.width(),
            "current_wheel": getattr(self, "current_wheel", None)
        }
        try:
            with open(settings_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.label = QLabel(self)
        image_path = self.current_wheel if self.current_wheel else os.path.join(self._wheels_dir, "steering_wheel.png")
        if os.path.exists(image_path):
            self.pixmap = QPixmap(image_path)
            self.original_pixmap = self.pixmap
            self.resized_pixmap = self.original_pixmap.scaled(
                self.dimension, self.dimension, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(self.resized_pixmap)
            self.resize(self.dimension, self.dimension)
        else:
            print(f"Image not found at: {image_path}")
            self.close()
            return
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        self.setWindowOpacity(self.opacity_value / 255)

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
        angle = x_axis * 270  # Calculate the angle
        
        # Only update if angle has changed significantly
        if abs(angle - self.last_angle) < 0.5:
            return
            
        self.last_angle = angle

        transform = QTransform()
        transform.translate(self.resized_pixmap.width() / 2, self.resized_pixmap.height() / 2)
        transform.rotate(angle)
        transform.translate(-self.resized_pixmap.width() / 2, -self.resized_pixmap.height() / 2)

        rotated_pixmap = self.resized_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # Only update if the pixmap has changed
        if rotated_pixmap.cacheKey() != self.label.pixmap().cacheKey():
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

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_settings_window()

    def show_settings_window(self):
        settings = SettingsWindow(self)
        settings.exec_()

    def update_opacity(self):
        self.setWindowOpacity(self.opacity_value / 255)
        self.save_settings()

    def change_wheel(self, new_wheel_path):
        if os.path.exists(new_wheel_path):
            self.pixmap = QPixmap(new_wheel_path)
            self.original_pixmap = self.pixmap
            self.resized_pixmap = self.original_pixmap.scaled(
                self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.current_wheel = new_wheel_path
            self.update_wheel()
            self.save_settings()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def setDimensions(self, size):
        self.resize(size, size)
        self.dimension = size
        if hasattr(self, 'original_pixmap'):
            self.resized_pixmap = self.original_pixmap.scaled(
                size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.update_wheel()
        self.save_settings()

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TransparentWindow()
    ex.show()
    sys.exit(app.exec_())