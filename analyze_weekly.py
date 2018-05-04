import sys
import csv
from datetime import datetime

shift = {}
trans = []

date = ""
#read the shift details and the bills
with open(sys.argv[1]) as f:
    rows = f.readlines()
s = 1
for row in rows:
    row = row.replace('\n','')
    if 'theyellow' in row:
        if s: date = row
        continue
    if 'Name' in row:
        keys = row.split(',')
        continue
    if 'REPORT' in row:
        s = 0
        continue
    row = row.replace('Admin', 'Kitchen')
    cols = row.split(',')
    cols1 = {}
    i = 0
    for col in cols:
        cols1[keys[i]] = col
        i += 1
    if s:
        if cols1['Staff Type'] == 'Owner': continue
        if shift.has_key(cols1['Name']):
            shift[cols1['Name']].append(cols1)
        else:
            shift[cols1['Name']] = [cols1]
    else:
        trans.append(cols1)

date = date.split('-')
total=8
lunch=9
dinner=10
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
report = {}
when = ['cur', 'last', 'avg']
for d in days:
    report[d] = {}
    for w in when:
        report[d][w] = {}
        for h in range(8,24):
            report[d][w][h] = {
                'sales'      : 0.0,
                'labor'      : 0.0,
                'orders'     : 0,
                'seats'      : 0,
                'servers'    : 0,
                'bartenter'  : 0,
                'busser'     : 0,
                'hostess'    : 0,
                'food-runner': 0,
            }
str = '\t,'
hdr = 'Time\t,'
stats = ''
for s in sorted(report['Mon']['cur'][8].keys()): stats += ','+s
for d in days:
    str += d + ',,,   ' 
    hdr += stats
print str
print hdr
for h in range(8,24):
    if h == 8:
        str = "Total"
    elif h == 9:
        str = "Lunch"
    elif h == 10:
        str = "Dinner"
    else:
        str = "%d:00-%d:00,"%(h,h+1)
    sys.stdout.write(str)
    for w in when:
        line = "\t,"+w+","
        for d in days:
            for s in sorted(report['Mon']['cur'][8].keys()):
                line += "%d"%report[d][w][h][s] + ","
        print line
