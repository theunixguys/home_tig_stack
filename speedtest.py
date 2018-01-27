#!/usr/bin/python3


##  Server ID,Sponsor,Server Name,Timestamp,Distance,Ping,Download,Upload
##
## 5029 is AT&T server in NYC
##

import subprocess
import time
import requests
influxAPI = 'http://127.0.0.1:8086/write?db=speedtest'

time.sleep(10)

myTime = time.time()
myTime = int(myTime)
myTimeNanoSecs = myTime * 1000000000

rawOutput = subprocess.check_output(['/usr/local/bin/speedtest-cli', '--csv', '--server', '5029'])
rawOutput = rawOutput.rstrip()
rawOutput = rawOutput.decode('utf-8')
print("output is", rawOutput)

## fixups
outputArray = rawOutput.split(',')
print(outputArray)

dl, ul = outputArray[7], outputArray[8]
dl = int(float(dl) / 1000000)
ul = int(float(ul) / 1000000)

payload2 = "speeds,host=vault2,remote_server=5029 download=" + str(dl) + " " + str(myTimeNanoSecs)
payload3 = "speeds,host=vault2,remote_server=5029 upload=" + str(ul) + " " + str(myTimeNanoSecs)

r = requests.post(influxAPI, data=payload2)
print(r.headers)
r = requests.post(influxAPI, data=payload3)
print(r.headers)
