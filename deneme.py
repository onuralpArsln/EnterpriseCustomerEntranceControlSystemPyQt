import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt

class ImageWidget(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.initUI(pixmap)

    def initUI(self, pixmap):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.imageLabel = QLabel()
        self.imageLabel.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        self.layout.addWidget(self.imageLabel)

        self.timerLabel = QLabel('Timer: 05:00')
        self.layout.addWidget(self.timerLabel)
        self.layout.setSpacing(2)  # Reduce spacing between image and timer

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.timeLeft = 300  # 5 minutes in seconds
        self.startTimer()

    def startTimer(self):
        self.timeLeft = 300  # 5 minutes in seconds
        self.updateTimerLabel()
        self.timer.start(1000)

    def updateTimer(self):
        self.timeLeft -= 1
        self.updateTimerLabel()
        if self.timeLeft == 0:
            self.timer.stop()

    def updateTimerLabel(self):
        minutes, seconds = divmod(self.timeLeft, 60)
        self.timerLabel.setText(f'Timer: {minutes:02}:{seconds:02}')

class ImageGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.images = []

        self.addButton = QPushButton('Add Image')
        self.addButton.clicked.connect(self.addImage)
        self.grid.addWidget(self.addButton, 0, 0, 1, 5)

        self.setFixedSize(520, 520)  # Set fixed size for the window
        self.setWindowTitle('Image Grid')
        self.show()

    def addImage(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        if fileName:
            pixmap = QPixmap(fileName)
            imageWidget = ImageWidget(pixmap)
            self.images.append(imageWidget)
            self.updateGrid()

    def updateGrid(self):
        for i in range(len(self.images)):
            self.grid.addWidget(self.images[i], (i // 5) + 1, i % 5)

        for i in range(len(self.images), 10):
            self.grid.addWidget(QLabel(), (i // 5) + 1, i % 5)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageGrid()
    sys.exit(app.exec_())