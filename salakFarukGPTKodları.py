import sys
import os
import cv2
import time
import numpy as np
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QWidget,
                             QStackedWidget, QSpinBox, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QComboBox, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QFileDialog, QListWidget,QGridLayout)
from PyQt5.QtGui import QImage, QPixmap,QPainter
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QSettings
import pickle

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
                font-size: 36px;
                color: #333;
                margin: 0px;
                padding: 0px;
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
        #left_panel.addWidget(QLabel('Şuanki Kullanıcılar:'))
        #left_panel.addWidget(self.user_list)

        # Ayarlar ve Geçmiş butonları
        settings_button = QPushButton('Ayarlar')
        settings_button.clicked.connect(self.show_settings)
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

        # ImageGrid widget
        self.image_grid = ImageGrid()
        capture_layout.addWidget(self.image_grid)

        
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
        #cam_pipeline_str = self.__gstreamer_pipeline(camera_id=0, flip_method=2)
        self.capture = cv2.VideoCapture(0)
        '''
        if not self.capture.isOpened():
            self.camera_label.setText("Kamera erişilemiyor!")
        else:
            self.timer = self.startTimer(30)
        '''
        # Kullanıcı zamanları
        self.photo_timestamps = {}

        # Zaman kontrolü
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_photo_timestamps)
        self.check_timer.start(1000)

        # Kullanıcıları yükle
        self.load_existing_users()
        self.time_limit_start()
        self.delete_timers()
        self.load_timers()

        self.count = 0
        self.name_input.setFocus()

    def timerEvent(self, event):
        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                # OpenCV'nin BGR formatından RGB formatına dönüştürme
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # NumPy dizisini QImage'e dönüştürme
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                # QImage'i QLabel'e koyma
                self.camera_label.setPixmap(QPixmap.fromImage(q_image))
            else:
                self.camera_label.setText("Kamera görüntüsü alınamıyor!")


    def update_scene_size(self):
        # Scene boyutlarını, fotoğrafların en son eklenen pozisyonuna göre ayarla
        if self.images:
            max_x = max(item.pos().x() + item.pixmap().width() for item in self.images)
            max_y = max(item.pos().y() + item.pixmap().height() for item in self.images)
            self.scene.setSceneRect(0, 0, max_x + 10, max_y + 10)  # Biraz boşluk ekle

            # View'ı güncelle ve fit et
            self.view.setSceneRect(self.scene.sceneRect())
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, photo BLOB, entry_date TEXT, time_limit INTEGER)''')
        self.db.commit()

    def save_settings(self):
        settings = QSettings("KralApp", "TimerSettings")  # Uygulama ve ayar adı
        settings.setValue("hour", self.hour_combo.currentText())
        settings.setValue("minute", self.minute_combo.currentText())
        settings.setValue("second", self.second_combo.currentText())
        self.update_time_limit()


    def load_settings(self):
        settings = QSettings("KralApp", "TimerSettings")
        hour = settings.value("hour", "0")  # Varsayılan: 1 saat
        minute = settings.value("minute", "0")  # Varsayılan: 0 dakika
        second = settings.value("second", "10")  # Varsayılan: 10 saniye

        self.hour_combo.setCurrentText(hour)
        self.minute_combo.setCurrentText(minute)
        self.second_combo.setCurrentText(second)

    def create_timetable(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS timetable
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, time DATETIME)''')
        self.db.commit()

    def load_user(self, item):
    # Kullanıcı adına tıklandığında, kullanıcı fotoğrafını yükle
        self.username = item.text()  # Listeden tıklanan kullanıcının adını al
        isim = self.username.split()[:-1]
        pathname = " ".join(isim)
        photo_path = f'users/{pathname}.jpg'  # Fotoğrafın yolu

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

    def time_limit_start(self):

        settings = QSettings("KralApp", "TimerSettings")
        hour = int(settings.value("hour", "0"))  # Varsayılan: 1 saat
        minute = int(settings.value("minute", "0"))  # Varsayılan: 0 dakika
        second = int(settings.value("second", "10"))  # Varsayılan: 10 saniye
        
        self.time_limit = (hour * 3600) + (minute * 60) + second

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

        index = next((i for i, image in enumerate(self.image_grid.images) if image.image_path == filename), -1)

        if index != -1:
            if self.image_grid.images[index].image_path == filename:
                if self.image_grid.images[index].gettime() <= 0:
                    self.save_to_database(filename)
                    self.image_grid.images[index].removeOverlay()
                    self.image_grid.images[index].removeTimerLabel()
                    self.image_grid.images.pop(index)
                    self.image_grid.updateGrid()
                else:
                    self.image_grid.images[index].setStopped()
            self.name_input.clear()
            self.name_input.setFocus()
            return
        


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

        #self.photo_timestamps[filename] = time.time()
        self.image_grid.addImage(filename, max(0, int(self.time_limit)))
        self.load_existing_users()
        self.name_input.clear()
        self.name_input.setFocus()
        #self.cursor.execute("INSERT INTO timetable (name, time) VALUES (?, ?)",
        #                    (filename, self.photo_timestamps[filename]))
        #self.db.commit()

    def save_black_image(self, filepath):
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)  # Siyah görüntü
        cv2.imwrite(filepath, black_image)

    def save_to_database(self, filename):
        if not filename:
            print("nononon")
            return

        photo_data = open(filename, 'rb').read()  # Fotoğrafı veritabanına ekle
        entry_date = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime(time.time()))
        self.cursor.execute("INSERT INTO users (name, photo, entry_date, time_limit) VALUES (?, ?, ?, ?)",
                            (filename, photo_data, entry_date, self.time_limit))
        
        if os.path.exists(filename):
            os.remove(filename)  # Dosyayı siliyoruz
            print(f"{filename} dosyası başarıyla silindi.")
            self.load_existing_users()
        else:
            print(f"{filename} dosyası bulunamadı.")

    def check_photo_timestamps(self):

        self.count = self.count + 1
        if self.count == 10:
            self.count = 0
            self.save_timers(self.image_grid.images)
            self.image_grid.images.sort(key=lambda image: image.timeLeft)
            self.image_grid.updateGrid()
        
            
        '''
        current_time = time.time()
        for filename, timestamp in list(self.photo_timestamps.items()):
            if current_time - timestamp > self.time_limit - 300:
                base_name = os.path.basename(filename)[:-4]
                items = self.user_list.findItems(base_name, Qt.MatchExactly)
                for item in items:
                    #item.setText(f"{base_name} ❗")
                    #item.setForeground(Qt.red)
                    #self.add_image(f"/users/{base_name}.jpg")
                    #print(f"{base_name} isimli kullanıcı {self.time_limit - (current_time - timestamp)} saniye içinde eklenmeli.")
                    self.image_grid.addImage(f"users/{base_name}.jpg", max(0, int(self.time_limit - (current_time - timestamp))))
                    # Yazıyı kalınlaştır
                    #font = item.font()
                    #font.setBold(True)
                    #item.setFont(font)
    '''
    def fillPhotoStamps(self):
        self.cursor.execute("SELECT * FROM timetable")
        rows = self.cursor.fetchall()
        for row in rows:
            self.photo_timestamps[row[1]] = row[2]
                

    def deleteDB(self):
        self.cursor.execute("DROP TABLE users")
        self.cursor.execute("DROP TABLE timetable")

    def show_history(self):
        # Önceki geçmiş ekranını kaldır (varsa)
        for i in range(self.stacked_widget.count()):
            if isinstance(self.stacked_widget.widget(i), QWidget) and self.stacked_widget.widget(i).layout() is not None:
                layout = self.stacked_widget.widget(i).layout()
                if isinstance(layout.itemAt(0).widget(), QTableWidget):
                    self.stacked_widget.removeWidget(self.stacked_widget.widget(i))
                    break

        # Yeni geçmiş sayfası oluştur
        history_page = QWidget()
        history_layout = QVBoxLayout()
        history_page.setLayout(history_layout)

        # Geçmiş kaydını tabloya ekle
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["İsim", "Fotoğraf", "Giriş Tarihi", "Süre"])
        history_layout.addWidget(table)

        # Veritabanından verileri al
        self.cursor.execute("SELECT * FROM users")
        rows = self.cursor.fetchall()
        for row in rows:
            photo_data = row[2]
            row_position = table.rowCount()
            table.insertRow(row_position)
            if photo_data:
                # BLOB verisini QPixmap nesnesine dönüştür
                photo = QPixmap()
                photo.loadFromData(photo_data)

                # Küçük boyutta göster
                photo = photo.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Fotoğrafı QLabel'e ekle
                photo_label = QLabel()
                photo_label.setPixmap(photo)

                # Fotoğrafı tablo hücresine yerleştir
                table.setCellWidget(row_position, 1, photo_label)
            
            table.setItem(row_position, 0, QTableWidgetItem(row[1]))  # İsim
            table.setItem(row_position, 2, QTableWidgetItem(row[3]))  # Giriş tarihi
            table.setItem(row_position, 3, QTableWidgetItem(str(row[4])))  # Süre

        # Geri dön butonu
        back_button = QPushButton('Geri Dön')
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        history_layout.addWidget(back_button)

        # Yeni geçmiş sayfasını ekle
        self.stacked_widget.addWidget(history_page)
        self.stacked_widget.setCurrentIndex(self.stacked_widget.count() - 1)

    def show_settings(self):
        settings_page = QWidget()
        settings_layout = QVBoxLayout()
        settings_page.setLayout(settings_layout)

        # Zaman sınırı başlığı
        title_label = QLabel('<b>Zaman Sınırı Ayarı:</b>')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; color: #333; margin-bottom: 15px;")
        settings_layout.addWidget(title_label)

        # Saat, dakika ve saniye layout
        time_setting_layout = QHBoxLayout()

        # Saat ComboBox
        self.hour_combo = QComboBox()
        self.hour_combo.addItems([str(i) for i in range(0, 9)])  # 1-8 saat
        self.hour_combo.setCurrentIndex(0)

        # Dakika ComboBox
        self.minute_combo = QComboBox()
        self.minute_combo.addItems(["0", "30", "60"])  # 0, 30, 60 dakika
        self.minute_combo.setCurrentIndex(0)

        # Saniye ComboBox
        self.second_combo = QComboBox()
        self.second_combo.addItems([str(i) for i in range(0, 60, 10)])  # 0'dan 50'ye kadar 10'un katları
        self.second_combo.setCurrentIndex(1)  # Varsayılan olarak 10 saniye
        self.load_settings()
        # Stil ayarları
        combo_style = """
        QComboBox {
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px 20px 5px 10px;
            font-size: 14px;
            color: #333;
            background-color: #f9f9f9;
        }
        QComboBox::drop-down {
            border-left: 1px solid #555;
            width: 30px;
            background-color: #eee;
        }
        QComboBox::down-arrow {
            image: url(icons/down_arrow.png); /* Aşağı ok simgesi */
            width: 12px;
            height: 12px;
        }
        QComboBox::up-arrow {
            image: url(icons/up_arrow.png); /* Yukarı ok simgesi */
            width: 12px;
            height: 12px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #555;
            selection-background-color: #0078d7;
            selection-color: #fff;
        }
        """
        self.hour_combo.setStyleSheet(combo_style)
        self.minute_combo.setStyleSheet(combo_style)
        self.second_combo.setStyleSheet(combo_style)

        # Saat: [ComboBox], Dakika: [ComboBox], Saniye: [ComboBox]
        hour_layout = QVBoxLayout()
        hour_label = QLabel("Saat:")
        hour_label.setAlignment(Qt.AlignCenter)
        hour_label.setStyleSheet("font-size: 14px; color: #333;")
        hour_layout.addWidget(hour_label)
        hour_layout.addWidget(self.hour_combo)

        minute_layout = QVBoxLayout()
        minute_label = QLabel("Dakika:")
        minute_label.setAlignment(Qt.AlignCenter)
        minute_label.setStyleSheet("font-size: 14px; color: #333;")
        minute_layout.addWidget(minute_label)
        minute_layout.addWidget(self.minute_combo)

        second_layout = QVBoxLayout()
        second_label = QLabel("Saniye:")
        second_label.setAlignment(Qt.AlignCenter)
        second_label.setStyleSheet("font-size: 14px; color: #333;")
        second_layout.addWidget(second_label)
        second_layout.addWidget(self.second_combo)

        # Layoutları yan yana ekle
        time_setting_layout.addLayout(hour_layout)
        time_setting_layout.addLayout(minute_layout)
        time_setting_layout.addLayout(second_layout)

        settings_layout.addLayout(time_setting_layout)

        # Geri dön butonu
        settings_back_button = QPushButton('Geri Dön')
        settings_back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        settings_layout.addWidget(settings_back_button, alignment=Qt.AlignCenter)

        # Ayarlar sayfasını ekle ve geçiş yap
        self.stacked_widget.addWidget(settings_page)
        self.stacked_widget.setCurrentWidget(settings_page)

        # Zaman sınırı güncellemeleri için sinyaller
        self.hour_combo.currentIndexChanged.connect(self.save_settings)
        self.minute_combo.currentIndexChanged.connect(self.save_settings)
        self.second_combo.currentIndexChanged.connect(self.save_settings)

    def update_time_limit(self):
        hours = int(self.hour_combo.currentText())
        minutes = int(self.minute_combo.currentText())
        seconds = int(self.second_combo.currentText())

        # Zaman sınırını saniyeye çevir
        self.time_limit = (hours * 3600) + (minutes * 60) + seconds
        print(f"Yeni zaman sınırı: {self.time_limit} saniye")

    def closeEvent(self, event):
        self.capture.release()
        self.db.close()

    def save_timers(self, my_list):
        settings = QSettings("KralApp", "TimerSettings")
        # Store only the necessary data for each image
        image_data = [(image.image_path, image.timeLeft, image.stopped) for image in my_list]
        settings.setValue("timers", pickle.dumps(image_data))
        print("Timers saved")

    def load_timers(self):

        settings = QSettings("KralApp", "TimerSettings")
        saved_data = settings.value("timers")
        if saved_data:
            image_data = pickle.loads(saved_data)
            
            for image_path, time_left, stopped in image_data:
                pixmap = QPixmap(image_path)
                imageWidget = ImageWidget(pixmap, time_left, image_path, stopped)
                self.image_grid.images.append(imageWidget)
                self.image_grid.updateGrid()
            print("Timers loaded")
    
    def delete_timers(self):
        settings = QSettings("KralApp", "TimerSettings")
        settings.remove("timers")
        print("Timers deleted")

class ImageGrid(QWidget):


    max_images = 10

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.images = []

        self.setFixedSize(1440, 1080)  # Set fixed size for the window
        self.setWindowTitle('Image Grid')
        self.show()

    def addImage(self, image_path, time):

        if not any(image.image_path == image_path for image in self.images):
            print(f"{image_path} fotoğrafı eklendi.")
            pixmap = QPixmap(image_path)
            imageWidget = ImageWidget(pixmap, time, image_path, False)
            self.images.append(imageWidget)
            self.updateGrid()
        else:
            pass

    

    def updateGrid(self):
        for i in range(min(len(self.images), 10)):
            self.grid.addWidget(self.images[i], (i // 5) + 1, i % 5)

        for i in range(min(len(self.images), 10)):
            self.grid.addWidget(QLabel(), (i // 5) + 1, i % 5)


class ImageWidget(QWidget):
    def __init__(self, pixmap, time_left, image_path, stopped):
        super().__init__()
        self.stopped = stopped
        self.image_path = image_path
        self.initUI(pixmap, time_left, image_path)


    def initUI(self, pixmap, time_left, image_path):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.imageLabel = QLabel()
        self.imageLabel.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio))
        self.imageLabel.setStyleSheet("margin: 0px; padding: 0px;")
        self.layout.addWidget(self.imageLabel)

        self.timerLabel = QLabel()
        self.timerLabel.setStyleSheet("""
            margin-bottom: 10px;
            margin-left: 15px;
            padding: 0px;
        """)
        self.layout.addWidget(self.timerLabel)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.timeLeft = time_left  
        self.startTimer(time_left)

    def startTimer(self, time_left):
        self.timeLeft = time_left 
        self.updateTimerLabel()
        self.timer.start(1000)

    def updateTimer(self):
        if self.timeLeft > 0 and self.stopped == False:
            self.timeLeft -= 1
        if self.timeLeft <= 0:
            self.overlay = QPixmap(self.imageLabel.pixmap().size())
            self.overlay.fill(Qt.red)
            painter = QPainter(self.overlay)
            painter.setOpacity(0.7)
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())
            painter.end()
            self.imageLabel.setPixmap(self.overlay)
            self.timer.stop()
        self.updateTimerLabel()
        

    def updateTimerLabel(self):
        minutes, seconds = divmod(int(self.timeLeft), 60)
        self.timerLabel.setText(f'{minutes:02}:{seconds:02}')
    
    def removeTimerLabel(self):
        self.timerLabel.setText('')

    def removeOverlay(self):
        if self.imageLabel is not None:
            self.layout.removeWidget(self.imageLabel)
            self.imageLabel.deleteLater()
            self.imageLabel = None

    def setStopped(self):
        self.stopped = not self.stopped

    def gettime(self):
        return self.timeLeft



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserPhotoCaptureApp()
    window.show()
    sys.exit(app.exec_())
