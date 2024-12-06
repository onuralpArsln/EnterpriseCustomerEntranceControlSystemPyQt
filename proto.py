import sys
import os
import cv2
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QWidget, QMessageBox, 
                             QListWidget, QStackedWidget, QSpinBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class UserPhotoCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('User Photo Management')
        self.setGeometry(100, 100, 800, 600)

        # Default time limit
        self.time_limit = 10

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left panel for user list
        left_panel = QVBoxLayout()
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.load_user)
        left_panel.addWidget(QLabel('Existing Users:'))
        left_panel.addWidget(self.user_list)

        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()

        # Camera capture page
        capture_page = QWidget()
        capture_layout = QVBoxLayout()
        capture_page.setLayout(capture_layout)

        # Camera feed label
        self.camera_label = QLabel()
        capture_layout.addWidget(self.camera_label)

        # Name input layout
        name_layout = QHBoxLayout()
        self.name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.returnPressed.connect(self.save_user_on_enter)
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        capture_layout.addLayout(name_layout)

        # User display page
        user_display_page = QWidget()
        user_display_layout = QVBoxLayout()
        user_display_page.setLayout(user_display_layout)
        
        # User photo label
        self.user_photo_label = QLabel()
        user_display_layout.addWidget(self.user_photo_label)
        
        # Back to capture button
        self.back_button = QPushButton('Back to Capture')
        self.back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        user_display_layout.addWidget(self.back_button)

        # Settings page
        settings_page = QWidget()
        settings_layout = QVBoxLayout()
        settings_page.setLayout(settings_layout)

        # Time limit setting
        settings_layout.addWidget(QLabel('Set Time Limit (seconds):'))
        self.time_limit_spinbox = QSpinBox()
        self.time_limit_spinbox.setRange(1, 60)
        self.time_limit_spinbox.setValue(self.time_limit)
        self.time_limit_spinbox.valueChanged.connect(self.update_time_limit)
        settings_layout.addWidget(self.time_limit_spinbox)

        # Back to capture button
        settings_back_button = QPushButton('Back to Capture')
        settings_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        settings_layout.addWidget(settings_back_button)

        # Add pages to stacked widget
        self.stacked_widget.addWidget(capture_page)
        self.stacked_widget.addWidget(user_display_page)
        self.stacked_widget.addWidget(settings_page)

        # Add layouts to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.stacked_widget, 3)

        # Settings button
        settings_button = QPushButton('Settings')
        settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        left_panel.addWidget(settings_button)

        # Initialize camera
        self.capture = cv2.VideoCapture(0)
        self.timer = self.startTimer(30)

        # Initialize photo timestamps
        self.photo_timestamps = {}

        # Setup time limit check timer
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_photo_timestamps)
        self.check_timer.start(1000)

        # Load existing users
        self.load_existing_users()

        # Set focus to name input when application starts
        self.name_input.setFocus()

    def load_existing_users(self):
        # Clear existing list
        self.user_list.clear()
        
        # Check if users directory exists
        if not os.path.exists('users'):
            os.makedirs('users')
        
        # Add users from directory
        for filename in os.listdir('users'):
            if filename.endswith('.jpg'):
                self.user_list.addItem(filename[:-4])

    def timerEvent(self, event):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), 
                                                      Qt.KeepAspectRatio))

    def save_user_on_enter(self):
        # Her enter tuşunda yeni bir fotoğraf çek
        ret, frame = self.capture.read()
        if not ret:
            return

        name = self.name_input.text().strip()
        if not name:
            return

        # Check if user already exists
        filename = f'users/{name}.jpg'
        if os.path.exists(filename):
            # Üzerine yazma onayı için kullanıcıya sormadan otomatik üzerine yaz
            pass

        # Save image
        cv2.imwrite(filename, frame)
        
        # Save timestamp
        self.photo_timestamps[filename] = time.time()
        
        # Reload users list
        self.load_existing_users()
        
        # Prepare for next entry
        self.name_input.clear()
        self.name_input.setFocus()  # Ensure focus remains on name input after saving

    def check_photo_timestamps(self):
        current_time = time.time()
        for filename, timestamp in list(self.photo_timestamps.items()):
            if current_time - timestamp > self.time_limit:
                QMessageBox.information(self, 'Photo Alert', f'Time limit exceeded for {os.path.basename(filename)}.')
                del self.photo_timestamps[filename]

    def update_time_limit(self, value):
        self.time_limit = value

    def load_user(self, item):
        # Load selected user's photo
        username = item.text()
        photo_path = f'users/{username}.jpg'
        
        # Display photo
        pixmap = QPixmap(photo_path)
        self.user_photo_label.setPixmap(pixmap.scaled(
            self.user_photo_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
        
        # Switch to user display page
        self.stacked_widget.setCurrentIndex(1)

    def closeEvent(self, event):
        self.capture.release()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = UserPhotoCaptureApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
