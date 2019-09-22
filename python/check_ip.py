import os
from datetime import datetime

#192.168.1.10 is the ip address

detach_dir = '.'
if 'logs' not in os.listdir(detach_dir):
    os.mkdir('logs')
time = datetime.now()
fname = 'logs/'+time.strftime('%Y_%B_%d_%A')+'.txt'
print fname
f = open(fname,"a")
ret = os.system("ping -o -c 10 -W 3000 10.0.0.179")
string = time.strftime('%I:%M %p = ')
if ret == 0:
    string += 'alive'
else:
    string += 'dead'
print string
f.write(string+'\n')
