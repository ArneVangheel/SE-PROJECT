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
brieven_count = getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken).json()["brief"]
pakketten_count = getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken).json()["pakketten"]

def lcd():
    global brieven_count
    global pakketten_count
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
        draw.text((1,0), ("Brieven: " + str(brieven_count)) , font=font)
        draw.text((1,8), ("Pakketen: " + str(pakketten_count)), font=font)
        # draw.text((1,24), (str(time_till_feeding)), font=font)
        # draw.text((1,32), (str(nummer)), font=font)
        display.image(image)
        display.show()

def timer():
    global brieven_count
    global pakketten_count
    while True:
        time.sleep(5)
        brieven_count = getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken).json()["brief"]
        pakketten_count = getrequest = requests.get("https://api-ensa-arnevangheel.cloud.okteto.net/counts", headers=headerswithtoken).json()["pakketten"]
        
thread1 = threading.Thread(target=lcd)
thread1.start()
thread2 = threading.Thread(target=timer)
thread2.start()
