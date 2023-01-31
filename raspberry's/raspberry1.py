import RPi.GPIO as GPIO
import threading
import time
import requests
import json
from urllib import request, parse
from time import sleep, strftime
import busio
import digitalio
import board
import adafruit_pcd8544
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

request_data = {
    "grant_type": '',
    "username": 'admin',
    "password": 'admin',
    "scope": '',
    "client_id": '',
    "client_secret": ''
}

tokenrequest = requests.post("https://api-ensa-arnevangheel.cloud.okteto.net/token", data=request_data)
token = json.loads(tokenrequest.text)['access_token']

headerswithtoken = {
    "accept": "application/json",
    "Authorization": f'Bearer {token}'
}

# drukknoppen
GPIO.setmode(GPIO.BCM)
pin26 = 26  # 26 # confirm knop
pin18 = 18  # 18
pin16 = 16  # 23 --> veranderd van 23 naar 16
pin13 = 13  # 24 --> veranderd van 24 naar 13
GPIO.setup(pin26, GPIO.IN)
GPIO.setup(pin18, GPIO.IN)
GPIO.setup(pin16, GPIO.IN)
GPIO.setup(pin13, GPIO.IN)

# steppermotor
pin22 = 22
pin27 = 27
pin25 = 25
pin5 = 5
pin12 = 12
GPIO.setup(pin22, GPIO.OUT)
GPIO.setup(pin27, GPIO.OUT)
GPIO.setup(pin25, GPIO.OUT)
GPIO.setup(pin5, GPIO.OUT)
GPIO.setup(pin12, GPIO.IN)

# push melding
# brief
pin17 = 17
GPIO.setup(pin17, GPIO.IN)
# pakket
pin6 = 6
GPIO.setup(pin6, GPIO.IN)

# global variabelen
correct_code = 110
send = False
count_zero_brief = 0
count_zero_pakket = 0

global code
global open_door
deur = False


def input_button():
    global code
    code = ""
    while True:
        time.sleep(0.1)
        if (GPIO.input(18) == 0):
            time.sleep(0.2)
            code += "1"
            print("1")

        if (GPIO.input(16) == 0):
            time.sleep(0.2)
            code += "2"
            print("2")

        if (GPIO.input(13) == 0):
            time.sleep(0.2)
            code += "3"
            print("3")

        if (GPIO.input(26) == 0):
            # time.sleep(6)
            print("---------")
            print(code)
            print("---------")
            check_code(code)
            code = ""


def check_code(code):
    getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/check_code/" + str(code),
                              headers=headerswithtoken)
    if getrequest.text == "false":
        print("foute code")
    else:
        print("juiste code")
        getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/check_code/" + str(code), headers=headerswithtoken)
        uses = getrequest.json()["uses"]
        if uses > 0:
            if uses == 1:
                getrequest = requests.delete("https://api-ensa-arnevangheel.cloud.okteto.net/code/" + str(code), headers=headerswithtoken)
                print("code verwijderd")
            else:
                data = {}
                data['uses'] = uses - 1
                getrequest = requests.put("https://api-ensa-arnevangheel.cloud.okteto.net/code/" + str(code), json=data, headers=headerswithtoken)
                print("Code aantal aangepast")
        global deur
        global send
        deur = True
        send = False
        getrequest = requests.put("https://api-ensa-arnevangheel.cloud.okteto.net/count/brief/" + str(0), headers=headerswithtoken)
        getrequest = requests.put("https://api-ensa-arnevangheel.cloud.okteto.net/count/pakketten/" + str(0), headers=headerswithtoken)
        linksom()


# stepper motor
def linksom():
    control_pins = [22, 27, 5, 25]
    for pin in control_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)
    halfstep_seq = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1]
    ]

    for i in range(135):
        for halfstep in range(8):
            for pin in range(4):
                GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)


def check_deur():
    global deur
    while True:
        if (GPIO.input(12) == 0):
            if deur == True:
                deur = False
                control_pins = [25, 5, 27, 22]
                for pin in control_pins:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, 0)
                halfstep_seq = [
                    [1, 0, 0, 0],
                    [1, 1, 0, 0],
                    [0, 1, 0, 0],
                    [0, 1, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 1],
                    [0, 0, 0, 1],
                    [1, 0, 0, 1]
                ]
                for i in range(135):
                    for halfstep in range(8):
                        for pin in range(4):
                            GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
                        time.sleep(0.001)


def pushmessage_brief():
    global send
    while True:
        time.sleep(0.2)
        if (GPIO.input(17) == 0):
            sendmessage_brief()
            getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken)
            aantal_brief = getrequest.json()["brief"]
            aantal_brief += 1
            getrequest = requests.put("https://api-ensa-arnevangheel.cloud.okteto.net/count/brief/" + str(aantal_brief), headers=headerswithtoken)
            print("brief gedetecteerd")
            time.sleep(1)


def sendmessage_brief():
    global send
    if send != True:
        send = True
        print("sms verzonden")
        # bericht versturen
        data = parse.urlencode({'key': 'YgS5Ls', 'title': 'Brievenbus', 'msg': 'Er is post.', 'event': 'Digitale Brievenbus'}).encode()
        req = request.Request("https://api.simplepush.io/send", data=data)
        request.urlopen(req)


def pushmessage_pakket():
    global send
    while True:
        time.sleep(0.2)
        if (GPIO.input(6) == 0):
            sendmessage_pakket()
            getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken)
            aantal_pakketten = getrequest.json()["pakketten"]
            aantal_pakketten += 1
            getrequest = requests.put("https://api-ensa-arnevangheel.cloud.okteto.net/count/pakketten/" + str(aantal_pakketten), headers=headerswithtoken)
            print("pakket gedetecteerd")
            time.sleep(1)


def sendmessage_pakket():
    global send
    if send != True:
        send = True
        print("sms verzonden")
        # bericht versturen
        data = parse.urlencode(
            {'key': 'YgS5Ls', 'title': 'Brievenbus', 'msg': 'Er is een post.', 'event': 'Digitale Brievenbus'}).encode()
        req = request.Request("https://api.simplepush.io/send", data=data)
        request.urlopen(req)


def lcd():
    global count_zero_brief
    global count_zero_pakket
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    # Initialize display
    dc = digitalio.DigitalInOut(board.D23)  # data/command
    cs1 = digitalio.DigitalInOut(board.CE1)  # chip select CE1 for display
    reset = digitalio.DigitalInOut(board.D24)  # reset
    display = adafruit_pcd8544.PCD8544(spi, dc, cs1, reset, baudrate= 1000000)
    display.bias = 4
    display.contrast = 30
    display.invert = True


#  Clear the display.  Always call show after changing pixels to make the display update visible!
    display.fill(0)
    display.show()
    # feed_time = datetime.datetime.now() + timedelta(seconds=10)

    while True:
        display.show()

        font = ImageFont.load_default()

        image = Image.new('1', (display.width, display.height)) 
        draw = ImageDraw.Draw(image)
                
        draw.rectangle((0, 0, display.width, display.height), outline=255, fill=255)
        # Write some text.
        nummer=4
        draw.text((1,0), ("Brieven: " + str(count_zero_brief)) , font=font)
        draw.text((1,8), ("Pakketen: " + str(count_zero_pakket)), font=font)
        # draw.text((1,24), (str(time_till_feeding)), font=font)
        # draw.text((1,32), (str(nummer)), font=font)
        display.image(image)
        display.show()


# Maken van Threads
thread1 = threading.Thread(target=input_button)
thread2 = threading.Thread(target=check_deur)
thread3 = threading.Thread(target=pushmessage_brief)
thread4 = threading.Thread(target=pushmessage_pakket)
thread5 = threading.Thread(target=lcd)

thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
