import sys
import csv
from datetime import datetime
import operator

shift = {'Kitchen' : [
    {'Name' : 'Kitchen',
     'Staff Type' : 'Kitchen',
     'Clock-In' : '2000-01-01 00:00',
     'Clock-Out': '2100-01-01 00:00',
     'Duration' : '0.0',
     'Hourly Rate' : '0.0',
     'Pay' : '0.0',
 } ]}
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

shared_tips= {
    # both breakage and BOH
    'Kitchen'  : 0.08,
    'Busser' : 0.10,
    'Food Runner' : 0.05,
    'Hostess' : 0.02,
    'Bartender': 0.05,
}

report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'pay':0.0, 'tips':0.0, 'cash':0.0}}
for u in shift.keys(): report[u] = {'type':shift[u][0]['Staff Type'],'hours':0.0, 'pay': 0.0, 'tips':0.0, 'cash':0.0}

for name, shifts in shift.iteritems():
    for s in shifts:
        report[name]['hours'] += float(s['Duration'])
        report[name]['pay'] += float(s['Pay'][1:])
# go over all the shift details
for t in trans:
    if t['Staff'] not in report.keys() :
        report['Kitchen']['tips'] += float(t['Tip'][1:])*0.7 + float(t['Gratuity'][1:])*0.7
    else:
        report[t['Staff']]['tips'] += float(t['Tip'][1:])*0.7 + float(t['Gratuity'][1:])*0.7
    if t['Name'] == 'Cash':
        report[t['Staff']]['cash'] += float(t['Payment Amount'][1:])

    #distribute the tips amongst the helpers
    for staff in shared_tips.keys():
        worked = 0
        for name, val in shift.iteritems():
            if val[0]['Staff Type'] != staff: continue
            #iterate over the shifts
            for s in val:
                tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
                fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                if  fr <= tran and tran <= to:
                    worked += 1
        if worked == 0:
            report['Kitchen']['tips'] += float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]
            continue
#            print "No one worked as " + staff + " for bill " + t['Bill Number'] + " at " + t['Bill Date']
        for name, val in shift.iteritems():
            if val[0]['Staff Type'] != staff: continue
            #iterate over the shifts
            for s in val:
                tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
                fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                if  fr <= tran and tran <= to:
                    report[name]['tips'] += (float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]) / worked
                


print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10}  {:<10} ".format('Name','Type', 'Hours','Pay', 'tips','cash-advance', 'Total')
hours, pay, tips, cash = 0.0, 0.0, 0.0, 0.0
for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
    print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10}  {:<10} ".format(k, v['type'], v['hours'], v['pay'], v['tips'], v['cash'], v['pay'] + v['tips']- v['cash'])
    hours += v['hours']
    pay += v['pay']
    tips += v['tips']
    cash += v['cash']
    
print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10}  {:<10} ".format("Total", "", hours, pay, tips, cash, hours+pay+tips-cash)
