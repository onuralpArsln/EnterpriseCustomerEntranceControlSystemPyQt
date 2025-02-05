import board
import busio
from adafruit_pn532.i2c import PN532_I2C
import time



#uart = serial.Serial("/dev/serial0", baudrate=115200, timeout=1)


i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug = False)

ic, ver, rev, support = pn532.firmware_version
print("format: {0}.{1}".format(ver,rev))

pn532.SAM_configuration()

user = input("Sayı: ")

def read():
    data = pn532.mifare_classic_read_block(6)  
    print("Okurken ki data burası: ", data)
    if data:
        data_dec = int("".join(f"{x:02X}" for x in data), 16)
        if data_dec == 0:
            print("kart boş")
            return 0
        else:
            print("data var")
            return data
    else:
        return 0


def clear():
    empty = bytearray([0x00] * 16)
    try:
        pn532.mifare_classic_write_block(6, empty)
        print("Temizleme başarılı.")
    except Exception as e:
        print("Temizlerken hata: ", e)

def write(uid ,number):
    number_str = str(number)
    byte_data = bytearray(number_str.encode('utf-8'))
    while len(byte_data) < 16:
        byte_data.append(0x00)
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    authenticated = pn532.mifare_classic_authenticate_block(uid, 6, 0x60, key)
    
    if not authenticated:
        print("Doğrulama başarısız")
        return
    else:
        print("Doğruladım")
    

    try:
        print(pn532.mifare_classic_write_block(6, byte_data))
        print("Yazma başarılı.")
    except Exception as e:
        print("Yazma hatalı: ", e)

while True:
    uid = pn532.read_passive_target(timeout=3)
    if uid is None:
        continue
    decimal = int("".join(f"{x:02X}" for x in uid), 16)
    print("Kart: ", decimal)
    deneme = int.from_bytes(uid, "little")
    deneme = str(deneme).zfill(10)
    print("UID: ", uid)
    print("Yeni Kart: ", deneme)
    data = read()
    if data == 0 or data == None:
        print("Salağım yazmaya girdim ve data: ", data)
        write(uid ,user)
    else:
        print("Data var ve: ", data)
        clear()
    time.sleep(2) 
