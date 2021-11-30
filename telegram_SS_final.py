import telepot      #library to link telegram bot
import time
import os
from picamera import PiCamera    #library to use PiCamera
import RPi.GPIO as GPIO 
import gspread                   #library to link google spreadsheet
import codecs                    #defines base classes for standard Python codec
import sys                         
from subprocess import call      
from oauth2client.service_account import ServiceAccountCredentials  #for pulling data from google sheets

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) 
path=os.getenv("HOME")
sensor = 16                   #PIR sensor connected to GPIO pin 16
BUZZER = 23                   #buzzer connected to GPIO pin 23
servoPIN = 17                 #servo motor connected to GPIO pin 17
GPIO.setup(sensor, GPIO.IN)   #GPIO pins setup as input or output pins
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(servoPIN, GPIO.OUT)


p = GPIO.PWM(servoPIN, 50)   #servo motor made as a PWM pin
p.start(2.5)                 #initialised 

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive'] #define the scope
creds = ServiceAccountCredentials.from_json_keyfile_name('securitysystemias-9d50af0cc222.json', scope)  #add credentials to the account
client = gspread.authorize(creds) #authorize the clientsheet 
sheet = client.open('loginandout') #get the instance of the Spreadsheet

def getWtv(datalist): #function to get a list of lists, where every list is a row from the Spreadsheet
    info=[]
    for rowdict in datalist:
        x=[]
        a=rowdict.get("Name").encode('ascii')
        b=rowdict.get("Time").encode('ascii')
        x.append(a)
        x.append(b)
        info.append(x)
    return info

def buzz(noteFreq, duration):                #customized buzzer sound
    halveWaveTime = 1 / (noteFreq * 2 )      #getting half time period from note freq.
    waves = int(duration * noteFreq)         #getting waves from freq.
    for i in range(waves):                   #for each wave buzzer is sounded for duration of note
       GPIO.output(BUZZER, True)
       time.sleep(halveWaveTime)             #buzzer made to sound for half time period
       GPIO.output(BUZZER, False)            #buzzer is turned off
       time.sleep(halveWaveTime)             #delay for half time period

def play():                     #to play custom sound
    t=0
    notes=[617, 824, 980, 873, 824, 1234, 1100, 925, 824, 980, 873, 777, 873, 617]  #notes of the tune
    duration=[1, 1.5, 0.5, 1, 2, 1, 2.5, 2.5, 1.5, 1, 1, 2, 1, 2.5]                 #duration of each note
    for n in notes:
        buzz(n, duration[t])                          #buzzer sounded for particular note and its duration
        time.sleep(duration[t] *0.1)                 #delay for duration of note
        t+=1

def handleMessage(msg):
    id = msg['chat']['id'];                     #id stores the bot and the id the message is received from
    command = msg['text'];                      #command stores the message that is received
    print ('Command ' + command + ' from chat id' + str(id));   #command is printed
   
    if (command == '/start'):                            #when the bot is started the welcome message is displayed
        bot.sendMessage(id,"Welcome to the Security Bot of XYZ society \n list of Commands :- \n /getinfo:- will return a list of people recognized in past 15 mins \n /motion :- motion sensing for 7 seconds if motion is detected you will recieve a photo or message stating that no one is there \n/buzzer:- emergency buzzer sound \n /opengates or /closegates :- to open or close  the gate \n /photo:- will send a live photo")

    elif(command=='/buzzer'):                            #the buzzer is sounded with play function
        bot.sendMessage(id,"Buzzer Initiated")           #message is sent to the bot that buzzer is initiated

        play()

    elif(command=='/opengate'):                          #gates are opened with help of servo motor
        bot.sendMessage(id,"Gates Opened ")             
        p.ChangeDutyCycle(7.5)                           #servo is made to rotate 90 degrees
        time.sleep(2)                                    #delay for 2 secs

    elif(command=='/closegate'):                         #gates are closed
        bot.sendMessage(id,"Gates Closed")
        p.ChangeDutyCycle(5)                             #servo rotated 90 degrees
        time.sleep(2)                                    #delay 2 secs

    elif(command=='/getinfo'):                          #get info gives information as to who all got in last
        bot.sendMessage(id,"The People Entered in the main gate in the last 15 mins are :- ")
        sheet_instance = sheet.get_worksheet(0)         # get the first sheet of the Spreadsheet

        records_data = sheet_instance.get_all_records() #list of dictionaries, where every dictionary is a row of the Spreadsheet
        y=getWtv(records_data)    
        
        print(y)
        bot.sendMessage(id,y)                           #sending function output to bot

    elif(command=='/photo'):                            #sends a photo to the telegram bot
        bot.sendMessage(id,"Sending Photo ....")
        camera = PiCamera();                            #Pi camera is started
        camera.start_preview()                          #camera is initialized
        camera.capture(path + '/piclive.jpg',resize=(640,480))     #picture is captured in path folder and resized
        time.sleep(2)                                   #delay of 2 sec
        camera.stop_preview()                           #camera is stopped
        camera.close()                                  #camera is closed
        bot.sendPhoto(id, open(path + '/piclive.jpg', 'rb'))     #the photo is sent to the bot in binary format
        time.sleep(0.1)                                 #delay of 100ms

    elif(command == '/motion'):                         #sends a photo if someone is detected in front of gate
        bot.sendMessage(id,"Checking If someone is There")    
        for a in range(7):                              #loop to check if anyone is there
            if (GPIO.input(sensor)==0):                 #if PIR sensor detects movement
                print ("Object Detected")               #object detected is printed
                camera = PiCamera();                    #Pi camera is started
                camera.start_preview()
                camera.capture(path + '/pic.jpg',resize=(640,480))   #photo is captured and resized in folder path
                time.sleep(2)                           #delay of 2 sec
                camera.stop_preview()         
                camera.close()                          #camera is closed
                bot.sendPhoto(id, open(path + '/pic.jpg', 'rb'))   #photo sent to telegram bot
                time.sleep(0.1) 
            else:                                       #if no motion is detected by PIR sensor
                bot.sendMessage(id,"No one is there")   #message sent to telegram bot
                print("No one is there")
                time.sleep(2)                           #delay for 2 secs

    
    else:
        bot.sendMessage(id, "Invalid Command try /start for list of all commands ")    #if unknown command received invalid command is sent to telegram bot
 
bot = telepot.Bot('AUTH TOKEN');            #the telegram bot is linked
bot.message_loop(handleMessage);                                                #the handle message to receive and check commands is looped
print ("Listening to bot message");                                             
while 1:                                                                        #main loop
    time.sleep(10);                                                             #delay for 10 sec
