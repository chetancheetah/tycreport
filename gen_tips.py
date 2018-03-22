import sys
import csv
from datetime import datetime

shift = {}
trans = []

with open(sys.argv[1]) as f:
    rows = f.readlines()
s = 1
for row in rows:
    row = row.replace('\n','')
    if 'theyellow' in row: continue
    if 'Name' in row:
        keys = row.split(',')
        continue
    if 'REPORT' in row:
        s = 0
        continue
    cols = row.split(',')
    cols1 = {}
    i = 0
    for col in cols:
        cols1[keys[i]] = col
        i += 1
    if s:
        if shift.has_key(cols[0]):
            shift[cols[0]].append(cols1)
        else:
            shift[cols[0]] = [cols1]
    else:
        trans.append(cols1)

shared_tips= {
    'Owner'  : 0.03,
    'Busser' : 0.10,
    'Food Runner' : 0.05,
    'Hostess' : 0.02,
    'BOH' : 0.05,
    'Bartender': 0.05,
}

report = {'Admin':{'hours':0.0, 'pay':0.0, 'tips':0.0, 'cash':0.0}}
for u in shift.keys(): report[u] = {'hours':0.0, 'pay': 0.0, 'tips':0.0, 'cash':0.0}

for name, shifts in shift.iteritems():
    for s in shifts:
        report[name]['hours'] += float(s['Duration'])
        report[name]['pay'] += float(s['Pay'][1:])
# go over all the shift details
for t in trans:
    report[t['Staff']]['tips'] += float(t['Tip'][1:])*0.7 + float(t['Gratuity'][1:])*0.7
    if t['Name'] == 'Cash':
        report[t['Staff']]['cash'] += float(t['Payment Amount'][1:])

    # now find how many similar employee worked at the same time.
    worked = 0
    for name, val in shift.iteritems():
        if val[0]['Staff Type'] not in shared_tips.keys(): continue
        #iterate over the shifts
        for s in val:
            tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
            fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
            to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
            if  fr <= tran and tran <= to:
                worked += 1
    for name, val in shift.iteritems():
        if val[0]['Staff Type'] not in shared_tips.keys(): continue
        #iterate over the shifts
        for s in val:
            tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
            fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
            to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
            if  fr <= tran and tran <= to:
                report[name]['tips'] += float(t['Tip'][1:])*shared_tips[s['Staff Type']] / worked
                

print "{:<30} {:<15} {:<15} {:<10}  {:<10}  {:<10} ".format('Name','Hours','Pay', 'tips','cash-advance', 'Total')
hours, pay, tips, cash = 0.0, 0.0, 0.0, 0.0
for k, v in report.iteritems():
    print "{:<30} {:<15} {:<15} {:<10}  {:<10}  {:<10}".format(k, v['hours'], v['pay'], v['tips'], v['cash'], v['pay'] + v['tips']- v['cash'])
    hours += v['hours']
    pay += v['pay']
    tips += v['tips']
    cash += v['cash']
    
print "{:<30} {:<15} {:<15} {:<10}  {:<10}  {:<10}".format("Total", hours, pay, tips, cash, hours+pay+tips+cash)
