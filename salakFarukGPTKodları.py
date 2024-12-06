import sys
import os
import cv2
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QWidget, QListWidget, 
                             QStackedWidget, QSpinBox, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class UserPhotoCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('User Photo Management')
        self.setGeometry(100, 100, 800, 600)  # Geniş pencere

        # Zaman sınırı
        self.time_limit = 10

        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Sol panel: Kullanıcı listesi
        left_panel = QVBoxLayout()
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.load_user)
        left_panel.addWidget(QLabel('Kayıtlı Kullanıcılar:'))
        left_panel.addWidget(self.user_list)

        # Ayarlar butonu
        settings_button = QPushButton('Ayarlar')
        settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        left_panel.addWidget(settings_button)

        # Sağ panel: Kamera ve diğer sayfalar
        self.stacked_widget = QStackedWidget()

        # Kamera sayfası
        capture_page = QWidget()
        capture_layout = QVBoxLayout()
        capture_page.setLayout(capture_layout)

        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)  # Kamera alanı
        self.camera_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        capture_layout.addWidget(self.camera_label)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('İsim:'))
        self.name_input = QLineEdit()
        self.name_input.returnPressed.connect(self.save_user_on_enter)
        name_layout.addWidget(self.name_input)
        capture_layout.addLayout(name_layout)

        # Kullanıcı gösterimi sayfası
        user_display_page = QWidget()
        user_display_layout = QVBoxLayout()
        user_display_page.setLayout(user_display_layout)

        self.user_photo_label = QLabel()
        self.user_photo_label.setMinimumSize(640, 480)
        user_display_layout.addWidget(self.user_photo_label)

        back_button = QPushButton('Geri Dön')
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        user_display_layout.addWidget(back_button)

        # Ayarlar sayfası
        settings_page = QWidget()
        settings_layout = QVBoxLayout()
        settings_page.setLayout(settings_layout)

        settings_layout.addWidget(QLabel('Zaman Sınırı Ayarı (saniye):'))
        self.time_limit_spinbox = QSpinBox()
        self.time_limit_spinbox.setRange(1, 60)
        self.time_limit_spinbox.setValue(self.time_limit)
        self.time_limit_spinbox.valueChanged.connect(self.update_time_limit)
        settings_layout.addWidget(self.time_limit_spinbox)

        settings_back_button = QPushButton('Geri Dön')
        settings_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        settings_layout.addWidget(settings_back_button)

        # Sayfaları ekle
        self.stacked_widget.addWidget(capture_page)
        self.stacked_widget.addWidget(user_display_page)
        self.stacked_widget.addWidget(settings_page)

        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.stacked_widget, 3)

        # Kamera başlat
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            self.camera_label.setText("Kamera erişilemiyor!")
        else:
            self.timer = self.startTimer(30)

        # Kullanıcı zamanları
        self.photo_timestamps = {}

        # Zaman kontrolü
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_photo_timestamps)
        self.check_timer.start(1000)

        # Kullanıcıları yükle
        self.load_existing_users()

    def load_existing_users(self):
        self.user_list.clear()
        if not os.path.exists('users'):
            os.makedirs('users')
        users = []
        for filename in os.listdir('users'):
            if filename.endswith('.jpg'):
                filepath = os.path.join('users', filename)
                mod_time = os.path.getmtime(filepath)
                users.append((mod_time, filename[:-4]))
        users.sort(reverse=True, key=lambda x: x[0])  # Tarihe göre sırala
        for _, username in users:
            self.user_list.addItem(username)

    def timerEvent(self, event):
        if not self.capture.isOpened():
            return
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
        name = self.name_input.text().strip()
        if not name:
            return

        filename = f'users/{name}.jpg'

        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                cv2.imwrite(filename, frame)
            else:
                QMessageBox.warning(self, "Hata", "Kamera görüntüsü alınamadı. Siyah bir görsel kaydediliyor.")
                self.save_black_image(filename)
        else:
            QMessageBox.warning(self, "Hata", "Kamera bağlantısı yok. Siyah bir görsel kaydediliyor.")
            self.save_black_image(filename)

        self.photo_timestamps[filename] = time.time()
        self.load_existing_users()
        self.name_input.clear()
        self.name_input.setFocus()

    def save_black_image(self, filepath):
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)  # Siyah görüntü
        cv2.imwrite(filepath, black_image)

    def check_photo_timestamps(self):
        current_time = time.time()
        for filename, timestamp in list(self.photo_timestamps.items()):
            if current_time - timestamp > self.time_limit:
                base_name = os.path.basename(filename)[:-4]
                items = self.user_list.findItems(base_name, Qt.MatchExactly)
                for item in items:
                    item.setText(f"{base_name} ❗")
                    item.setForeground(Qt.red)

    def update_time_limit(self, value):
        self.time_limit = value

    def load_user(self, item):
        username = item.text().split(' ❗')[0]
        photo_path = f'users/{username}.jpg'
        pixmap = QPixmap(photo_path)
        self.user_photo_label.setPixmap(pixmap.scaled(
            self.user_photo_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
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
