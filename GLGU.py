import RPi.GPIO as GPIO
import time
import threading

dataPin = 16
latchPin = 6
clockPin = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup((dataPin,latchPin,clockPin),GPIO.OUT)

matrix = [[0 for _ in range(8)] for _ in range(16)]

MSBFIRST = 1
LSBFIRST = 2

def shiftOut(dataPin, clockPin, bitOrder, val, bits):
	for i in range(bits):
		if bitOrder == MSBFIRST:
			bit = (val & (1 << (bits -1 -i))) >> (bits -1 -i)
		else:
			bit = (val & (1 <<i)) >>i
			
		GPIO.output(dataPin,bit)
		GPIO.output(clockPin, GPIO.HIGH)
		time.sleep(0.00001)
		GPIO.output(clockPin, GPIO.LOW)
		
row = [0b10000000,0b01000000,0b00100000,0b00010000,0b00001000,0b00000100,0b00000010,0b00000001]


#GLGU
col = [0b0101011100010111,0b0101000100010001,0b0101000100010001,0b0101000100010001,0b0101010100010101,0b0101010100010101,0b0101010100010101,0b0111011101110111]

#col = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]

def  refresh_display():
	for i in range(8):
		GPIO.output(latchPin,GPIO.LOW);
		shiftOut(dataPin,clockPin,LSBFIRST,col[i],16)
		shiftOut(dataPin,clockPin,LSBFIRST,row[i],8)
		
		GPIO.output(latchPin,GPIO.HIGH)
		time.sleep(0.00001)
		
	GPIO.output(latchPin,GPIO.LOW);	
	shiftOut(dataPin,clockPin,LSBFIRST,0x00,8)
	shiftOut(dataPin,clockPin,LSBFIRST,0x00,16)
	GPIO.output(latchPin,GPIO.HIGH)
	time.sleep(0.00001)
	
def refresh_display_for_threading():
	while True:
		refresh_display()
		
'''		
display_thread = threading.Thread(target=refresh_display_for_threading)
display_thread.start()


while True:
	for j in range(8):
		for i in range(16):
			col[j] = 1 << i
			time.sleep(0.02)
		col[j] = 0x00
'''
while True:
	refresh_display()
