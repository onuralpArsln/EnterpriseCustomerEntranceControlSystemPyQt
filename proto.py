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

        # Add pages to stacked widget
        self.stacked_widget.addWidget(capture_page)
        self.stacked_widget.addWidget(user_display_page)

        # Add layouts to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.stacked_widget, 3)

        # Initialize camera
        self.capture = cv2.VideoCapture(0)
        self.timer = self.startTimer(30)

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
        
        # Reload users list
        self.load_existing_users()
        
        # Prepare for next entry
        self.name_input.clear()
        self.name_input.setFocus()  # Ensure focus remains on name input after saving

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