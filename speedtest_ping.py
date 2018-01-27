#!/usr/bin/python3


##  Server ID,Sponsor,Server Name,Timestamp,Distance,Ping,Download,Upload
##
## 5029 is AT&T server in NYC
## 935 = DC
## 12625 - west chester

import subprocess
import time
import requests
influxAPI = 'http://127.0.0.1:8086/write?db=speedtest'

myTime = time.time()
myTime = int(myTime)
myTimeNanoSecs = myTime * 1000000000

id = {
    '72.21.92.82': '5029',
    '172.217.13.68': '1111',
    '24.53.144.10': '12625',
    '173.193.195.148': '935',
}

for host,code in id.items():
   rawOutput = subprocess.check_output(['/bin/ping', '-c', '5', '-i', '0.2', '-q', host])
   rawOutput = rawOutput.rstrip()
   rawOutput = rawOutput.decode('utf-8')

   outputArray = rawOutput.split('/')

   ping = outputArray[4]
   ping = int(float(ping))

   payload1 = "pings,host=vault2,remote_server=" + code + " ping=" + str(ping) + " " + str(myTimeNanoSecs)

   r = requests.post(influxAPI, data=payload1)
   print(r.headers)
