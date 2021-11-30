import numpy as np
import face_recognition as fr
import cv2
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('securitysystemias-9d50af0cc222.json', scope)

# authorize the clientsheet
client = gspread.authorize(creds)


# get the instance of the Spreadsheet
sheet = client.open('Loginandout')

# get the first sheet of the Spreadsheet
sheet_instance = sheet.get_worksheet(0)


path = 'images'     # images is just the name of the folder which contains the photos used to recognize the faces
images = []
classNames = []
myList = os.listdir(path)
print(myList)

for cl in myList:   # loop to add all the images of our dataset in a list by splitting out the the jpg from the list
     curImg = cv2.imread(f'{path}/{cl}')
     images.append(curImg)
     classNames.append(os.path.splitext(cl)[0])

print(classNames)


def findEncodings(images):  # finds the encodings of the images
     encodeList = []
     for img in images:
         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
         encode = fr.face_encodings(img)[0]
         encodeList.append(encode)
     return encodeList

def updateName(name):
    nameList = sheet_instance.col_values(1)

    if name not in nameList:
        now = datetime.now()
        dtString = now.strftime('%H:%M:%S')
        sheet_instance.append_row([name,dtString])


encodeListKnown = findEncodings(images)
print('Encoding complete')

cap = cv2.VideoCapture(0)       # the command to turn on the default camera of the device being used

while True:                    # the video feed received from your camera
    success, img = cap.read()
    imgS = cv2.resize(img, (0,0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    facesCurFrame = fr.face_locations(imgS)
    encodesCurFrame = fr.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = fr.compare_faces(encodeListKnown, encodeFace)
        faceDis = fr.face_distance(encodeListKnown, encodeFace)
        #print(faceDis)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex] >0.5:
            name = classNames[matchIndex].upper()
            #print(name)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            updateName(name)
        else:
            name = 'unknown'
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            updateName(name)


    cv2.imshow('webcam', img)
    cv2.waitKey(1)
