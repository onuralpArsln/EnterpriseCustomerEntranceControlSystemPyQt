import sys
import os
import cv2
import time
import numpy as np
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QWidget, QListWidget, 
                             QStackedWidget, QSpinBox, QMessageBox, QTableWidget, 
                             QTableWidgetItem)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class UserPhotoCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('User Photo Management')
        self.setGeometry(100, 100, 800, 600)

        # ** Genel Stil Uygulaması **
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f5;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #397d3f;
            }
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
                color: #333;
            }
            QListWidget {
                border: 2px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
                color: #333;
                background-color: #fff;
            }
            QTableWidget {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #fff;
            }
        """)

        self.time_limit = 10
        self.time_start = None

        # Veritabanı bağlantısı
        self.db = sqlite3.connect('user_photos.db')
        self.cursor = self.db.cursor()
        self.create_table()
        self.create_timetable()

        # Ana layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Sol panel
        left_panel = QVBoxLayout()

        # Kullanıcı listesi
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.load_user)
        left_panel.addWidget(QLabel('Şuanki Kullanıcılar:'))
        left_panel.addWidget(self.user_list)

        # Ayarlar ve Geçmiş butonları
        settings_button = QPushButton('Ayarlar')
        settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        left_panel.addWidget(settings_button)

        history_button = QPushButton('Geçmiş')
        history_button.clicked.connect(self.show_history)
        left_panel.addWidget(history_button)

        main_layout.addLayout(left_panel, 1)

        # Sağ panel
        self.stacked_widget = QStackedWidget()

        # Kamera sayfası
        capture_page = QWidget()
        capture_layout = QVBoxLayout()
        capture_page.setLayout(capture_layout)

        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #000;
                color: #fff;
                font-size: 16px;
                border: 3px solid #4CAF50;
                border-radius: 10px;
            }
        """)
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

        self.save_button = QPushButton('Tamam')
        self.save_button.clicked.connect(self.save_to_database)
        user_display_layout.addWidget(self.save_button)

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
        self.fillPhotoStamps()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, photo BLOB, entry_date TEXT, time_limit INTEGER)''')
        self.db.commit()

    def create_timetable(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS timetable
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, time DATETIME)''')
        self.db.commit()

    def load_user(self, item):
    # Kullanıcı adına tıklandığında, kullanıcı fotoğrafını yükle
        self.username = item.text()  # Listeden tıklanan kullanıcının adını al
        photo_path = f'users/{self.username}.jpg'  # Fotoğrafın yolu

    # Fotoğrafı göster
        if os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            self.user_photo_label.setPixmap(pixmap.scaled(self.user_photo_label.size(), 
                                                        Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fotoğraf yoksa, siyah bir görsel koy
            empty_pixmap = QPixmap(self.camera_label.size())  # Siyah bir görsel oluştur
            empty_pixmap.fill(Qt.black)  # Siyah renkle doldur
            self.user_photo_label.setPixmap(empty_pixmap)
        
        # Kullanıcı fotoğraf sayfasına geçiş yap
        self.stacked_widget.setCurrentIndex(1)


    def load_existing_users(self):
        self.user_list.clear()
        users = []
        for filename in os.listdir('users'):
            if filename.endswith('.jpg'):
                filepath = os.path.join('users', filename)
                mod_time = os.path.getmtime(filepath)
                users.append((mod_time, filename[:-4]))
        users.sort(reverse=True, key=lambda x: x[0])  # Tarihe göre sırala
        for _, username in users:
            self.user_list.addItem(username)

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
        self.cursor.execute("INSERT INTO timetable (name, time) VALUES (?, ?)",
                            (filename, self.photo_timestamps[filename]))
        self.db.commit()

    def save_black_image(self, filepath):
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)  # Siyah görüntü
        cv2.imwrite(filepath, black_image)

    def save_to_database(self):
        name = self.username.split()
        name = name[0]
        if not name:
            print("nononon")
            return

        filename = f'users/{name}.jpg'
        print(name)
        photo_data = open(filename, 'rb').read()  # Fotoğrafı veritabanına ekle
        entry_date = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime(time.time()))
        self.cursor.execute("INSERT INTO users (name, photo, entry_date, time_limit) VALUES (?, ?, ?, ?)",
                            (name, photo_data, entry_date, self.time_limit))
        

        sql = 'DELETE FROM timetable WHERE name = ?'
        self.cursor.execute(sql, (name,))
        self.db.commit()
        self.load_existing_users()  # Listeyi güncelle
        self.stacked_widget.setCurrentIndex(0)  # Ana sayfaya dön
        if os.path.exists(filename):
            os.remove(filename)  # Dosyayı siliyoruz
            print(f"{filename} dosyası başarıyla silindi.")
            self.load_existing_users()
        else:
            print(f"{filename} dosyası bulunamadı.")

    def check_photo_timestamps(self):
        current_time = time.time()
        for filename, timestamp in list(self.photo_timestamps.items()):
            if current_time - timestamp > self.time_limit:
                base_name = os.path.basename(filename)[:-4]
                items = self.user_list.findItems(base_name, Qt.MatchExactly)
                for item in items:
                    item.setText(f"{base_name} ❗")
                    item.setForeground(Qt.red)
                    
                    # Yazıyı kalınlaştır
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

    def fillPhotoStamps(self):
        self.cursor.execute("SELECT * FROM timetable")
        rows = self.cursor.fetchall()
        for row in rows:
            self.photo_timestamps[row[1]] = row[2]
                

    def deleteDB(self):
        self.cursor.execute("DROP TABLE users")
        self.cursor.execute("DROP TABLE timetable")

    def show_history(self):
        history_page = QWidget()
        history_layout = QVBoxLayout()
        history_page.setLayout(history_layout)

        # Geçmiş kaydını tabloya ekle
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["İsim", "Fotoğraf", "Giriş Tarihi", "Süre"])
        history_layout.addWidget(table)

        self.cursor.execute("SELECT * FROM users")
        rows = self.cursor.fetchall()
        for row in rows:
            print(row[0])
            photo_data = row[2]
            row_position = table.rowCount()
            table.insertRow(row_position)
            if photo_data:
            # BLOB verisini QPixmap nesnesine dönüştür
                photo = QPixmap()
                photo.loadFromData(photo_data)

                # Küçük boyutta göster
                photo = photo.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Fotoğrafı QLabel'e ekleyelim
                photo_label = QLabel()
                photo_label.setPixmap(photo)

                photo_label = QLabel()
                photo_label.setPixmap(photo)

                # Fotoğrafı tablo hücresine yerleştir
                table.setCellWidget(row_position, 1, photo_label)
            
            table.setItem(row_position, 0, QTableWidgetItem(row[1]))  # İsim
            #table.setItem(row_position, 1, QTableWidgetItem(f"Fotoğraf - {row[1]}"))
            table.setItem(row_position, 2, QTableWidgetItem(row[3]))  # Giriş tarihi
            table.setItem(row_position, 3, QTableWidgetItem(str(row[4])))  # Süre

            # Geri dön butonu
        back_button = QPushButton('Geri Dön')
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        history_layout.addWidget(back_button)

        self.stacked_widget.addWidget(history_page)
        self.stacked_widget.setCurrentIndex(3)

    def update_time_limit(self):
        self.time_limit = self.time_limit_spinbox.value()

    def closeEvent(self, event):
        self.capture.release()
        self.db.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserPhotoCaptureApp()
    window.show()
    sys.exit(app.exec_())
