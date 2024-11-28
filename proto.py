import sys
import os
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QWidget, QMessageBox, 
                             QListWidget, QStackedWidget)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class UserPhotoCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('User Photo Management')
        self.setGeometry(100, 100, 800, 600)

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

        # Buttons layout
        button_layout = QHBoxLayout()
        self.snap_button = QPushButton('Snap Photo')
        self.snap_button.clicked.connect(self.snap_photo)
        button_layout.addWidget(self.snap_button)

        self.add_user_button = QPushButton('Add New User')
        self.add_user_button.clicked.connect(self.add_new_user)
        self.add_user_button.setEnabled(False)
        button_layout.addWidget(self.add_user_button)

        capture_layout.addLayout(button_layout)

        # Name input layout
        name_layout = QHBoxLayout()
        self.name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        capture_layout.addLayout(name_layout)

        # Save button
        self.save_button = QPushButton('Save User')
        self.save_button.clicked.connect(self.save_user)
        self.save_button.setEnabled(False)
        capture_layout.addWidget(self.save_button)

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

        # Add pages to stacked widget
        self.stacked_widget.addWidget(capture_page)
        self.stacked_widget.addWidget(user_display_page)

        # Add layouts to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.stacked_widget, 3)

        # Initialize camera
        self.capture = cv2.VideoCapture(0)
        self.captured_image = None
        self.timer = self.startTimer(30)

        # Load existing users
        self.load_existing_users()

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

    def snap_photo(self):
        ret, frame = self.capture.read()
        if ret:
            self.captured_image = frame
            self.snap_button.setEnabled(False)
            self.save_button.setEnabled(True)
            self.name_input.setEnabled(True)
            QMessageBox.information(self, 'Photo Captured', 'Photo has been captured. Enter name and save.')

    def save_user(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'Error', 'Please enter a name')
            return

        # Check if user already exists
        if os.path.exists(f'users/{name}.jpg'):
            reply = QMessageBox.question(self, 'User Exists', 
                                         'A user with this name already exists. Overwrite?', 
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Save image
        filename = f'users/{name}.jpg'
        cv2.imwrite(filename, self.captured_image)

        QMessageBox.information(self, 'Success', f'User {name} saved successfully')
        
        # Reload users list and reset capture
        self.load_existing_users()
        self.add_new_user()

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

    def add_new_user(self):
        # Reset everything for a new user
        self.name_input.clear()
        self.name_input.setEnabled(False)
        self.save_button.setEnabled(False)
        self.snap_button.setEnabled(True)
        self.add_user_button.setEnabled(False)
        self.captured_image = None
        
        # Switch back to camera capture page
        self.stacked_widget.setCurrentIndex(0)

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