#!/usr/bin/python3

## this takes a raw data file from Ecobee and inserts into Influx

import subprocess
import time
import datetime
import requests
influxAPI = 'http://127.0.0.1:8086/write?db=hvac'


with open('hvac.csv') as myFile:
    contents = myFile.readlines()
    print(contents)

lastTime = 100
lastIncrement = 0

for line in contents:
    ## bypass header lines, blank lines, comment lines, and lines where no heating or cooling is active
    if line.startswith("Date") or line.startswith("#") or ",,," in line or line.strip() == "":
        continue
    hvacFields = line.split(',')
    myDate = hvacFields[0]
    myTime = hvacFields[1]
    myDateTime = myDate + ' ' + myTime
    myMode = hvacFields[3]
    mySetpoint = hvacFields[6]
    myOutdoorTemp = hvacFields[10]
    myStg1Seconds = hvacFields[12]
    myStg2Seconds = hvacFields[13]
    myHeatStg1Seconds = hvacFields[14]
    myHeatStg2Seconds = hvacFields[15]
    myOutdoorTemp = hvacFields[10]
    myFloorTemp1 = hvacFields[18]
    myHumidity = hvacFields[19]
    myFloorTemp2 = hvacFields[21]

    myStg1SecondsInt = int(myStg1Seconds)
    myStg2SecondsInt = int(myStg2Seconds)
    myStg1Pct = int(myStg1SecondsInt / 6)
    myStg2Pct = int(myStg2SecondsInt / 6)
    myLoad = myStg1Pct + myStg2Pct

    myHeatStg1SecondsInt = int(myHeatStg1Seconds)
    myHeatStg2SecondsInt = int(myHeatStg2Seconds)
    myHeatStg1Pct = int(myHeatStg1SecondsInt / 6)
    myHeatStg2Pct = int(myHeatStg2SecondsInt / 6)
    myHeatLoad = myHeatStg1Pct + myHeatStg2Pct

#    print("stg1 seconds is ", myStg1SecondsInt)
#    print("stg2 seconds is ", myStg2SecondsInt)
#    print("stg1 percent is ", myStg1Pct)
#    print("stg2 percent is ", myStg2Pct)
#    print("load is ", myLoad)
    timeFormat = "%Y-%m-%d %H:%M:%S"
    mydt = int(time.mktime(time.strptime(myDateTime, timeFormat)))
    mydtNanoSecs = mydt * 1000000000
    if mydtNanoSecs == lastTime:
       if lastIncrement:
          mydtNanoSecs = lastIncrement + 2000000000
          lastIncrement = mydtNanoSecs
       else:
          mydtNanoSecs = mydtNanoSecs + 2000000000
          lastIncrement = mydtNanoSecs
    else:
       lastTime = mydtNanoSecs
       lastIncrement = mydtNanoSecs

    payload1 = "hvacdata,location=sidley setpoint=" + str(mySetpoint) + " " + str(mydtNanoSecs)
    payload2 = "hvacdata,location=sidley outdoor=" + str(myOutdoorTemp) + " " + str(mydtNanoSecs)
    payload3 = "hvacdata,location=sidley floor1=" + str(myFloorTemp1) + " " + str(mydtNanoSecs)
    payload4 = "hvacdata,location=sidley floor2=" + str(myFloorTemp2) + " " + str(mydtNanoSecs)
    payload5 = "hvacdata,location=sidley humidity=" + str(myHumidity) + " " + str(mydtNanoSecs)
    payload6 = "hvacdata,location=sidley load=" + str(myLoad) + " " + str(mydtNanoSecs)
    payload7 = "hvacdata,location=sidley heatload=" + str(myHeatLoad) + " " + str(mydtNanoSecs)

    r = requests.post(influxAPI, data=payload1)
    r = requests.post(influxAPI, data=payload2)
    r = requests.post(influxAPI, data=payload3)
    r = requests.post(influxAPI, data=payload4)
    r = requests.post(influxAPI, data=payload5)
    r = requests.post(influxAPI, data=payload6)
    r = requests.post(influxAPI, data=payload7)
    #print(r.headers)
    print(mydtNanoSecs)
    print(payload1)
    print(payload2)
    print(payload3)
    print(payload4)
    print(payload5)
    print(payload6)
    print(payload7)
