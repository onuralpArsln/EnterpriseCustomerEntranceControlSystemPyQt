import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
import nfc

class NFCReader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.nfc_reader = nfc.ContactlessFrontend('usb')

    def initUI(self):
        self.layout = QVBoxLayout()

        self.label = QLabel('Enter a number:')
        self.layout.addWidget(self.label)

        self.number_input = QLineEdit(self)
        self.layout.addWidget(self.number_input)

        self.read_button = QPushButton('Read NFC Tag', self)
        self.read_button.clicked.connect(self.read_nfc_tag)
        self.layout.addWidget(self.read_button)

        self.setLayout(self.layout)
        self.setWindowTitle('NFC Reader')
        self.show()

    def read_nfc_tag(self):
        user_number = self.number_input.text()
        if not user_number.isdigit():
            self.label.setText('Please enter a valid number.')
            return

        self.label.setText('Waiting for NFC tag...')
        self.nfc_reader.connect(rdwr={'on-connect': lambda tag: self.on_tag_connect(tag, user_number)})

    def on_tag_connect(self, tag, user_number):
        uid = tag.identifier.hex()
        if tag.ndef:
            records = tag.ndef.records
            if records:
                self.label.setText(f'Tag UID: {uid}\nData: {records[0].text}')
                tag.ndef.records = []
            else:
                self.label.setText(f'Tag UID: {uid}\nNo additional data found. Writing user number...')
                tag.ndef.records = [nfc.ndef.TextRecord(user_number)]
        else:
            self.label.setText(f'Tag UID: {uid}\nNo NDEF support.')

        return False  # Disconnect after reading

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NFCReader()
    sys.exit(app.exec_())