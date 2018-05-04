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
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
report = {}

tw = datetime.now().isocalendar()[1]
for d in days:
    report[d] = {}
    for w in range(tw-5,tw+1):
        report[d][w] = {}
        for h in range(8,24):
            report[d][w][h] = {
                'sales'      : 0.0,
                'labor'      : 0.0,
#                'orders'     : 0,
#                'seats'      : 0,
                'Server'     : 0,
                'Bartender'  : 0,
                'Busser'     : 0,
                'Hostess'    : 0,
                'Food Runner': 0,
            }

for i in shift:
    for s in shift[i]:
        fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
        to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
        wd = fr.strftime("%A")
        week = fr.isocalendar()[1]
        t = s['Staff Type']
        if t not in report[wd][week][fr.hour].keys(): continue
        report[wd][week][8][t] += 1
        pay = float(s['Pay'][1:])
        report[wd][week][8]['labor'] += pay
        if to.hour < 18:
            report[wd][week][9][t] += 1
            report[wd][week][9]['labor'] += pay
        else:
            report[wd][week][10][t] += 1
            report[wd][week][10]['labor'] += pay
        for i in range(fr.hour, to.hour+1):
            report[wd][week][i][t] += 1

for t in trans:
    tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
    wd = tran.strftime("%A")
    week = tran.isocalendar()[1]
    amt = float(t['Applied to Bill'][1:])/1.09
    report[wd][week][8]['sales'] += amt
    if tran.hour < 18:
        report[wd][week][9]['sales'] += amt
    else:
        report[wd][week][10]['sales'] += amt

str = ','
hdr = 'Time,,'
#stats = 'sales,labor,orders,seats,Staff(S/B/B/H/F),'
stats = 'sales,labor,Staff(S/B/B/H/F),'
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
        str = "%d:00-%d:00"%(h,h+1)
    sys.stdout.write(str)
    for w in range(tw-5,tw+1):
        line = "\t,"+("week-%d"%w)+","
        for d in days:
            #stats = 'sales,labor,orders,seats,Staff(S/B/B/H/F),'
            line += "%d,%d,(%d/%d/%d/%d/%d),"%(
                report[d][w][h]['sales'],
                report[d][w][h]['labor'],
#                report[d][w][h]['orders'],
#                report[d][w][h]['seats'],
                report[d][w][h]['Server'],
                report[d][w][h]['Bartender'],
                report[d][w][h]['Busser'],
                report[d][w][h]['Hostess'],
                report[d][w][h]['Food Runner'], )
        print line
