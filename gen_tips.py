import sys
import csv
from datetime import datetime
import operator
import subprocess
import json

result = subprocess.check_output(['curl', 'https://api.7shifts.com/v1/users',  '-u', 'VS5RDPW86QD5X2A6D2YZT56VM9CLE3D8:'])
result = json.loads(result)

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

#read the shift details and the bills
with open(sys.argv[2]) as f:
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

#how to share
shared_tips= {
    'Kitchen'  : 0.08,   #  8%
    'Busser' : 0.10,     # 10%
    'Food Runner' : 0.05,#  5%
    'Hostess' : 0.02,    #  2%
    'Bartender': 0.05,   #  5%
}

report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}

for u in shift.keys(): report[u] = {'type':shift[u][0]['Staff Type'],'hours':0.0, 'pay': 0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}

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
                if s['Clock-Out'] == "\"\"":
                    to = datetime.now()
                else:
                    to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                if  fr <= tran and tran <= to:
                    worked += 1
        if worked == 0:
            # if there was no busser  or food runner then assumption the server would have bussed
            if staff == 'Busser' or staff == 'Food Runner':
                report[t['Staff']]['extra-tips'] += float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]
            else:
                report['Kitchen']['tips'] += float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]
            continue
#            print "No one worked as " + staff + " for bill " + t['Bill Number'] + " at " + t['Bill Date']
        for name, val in shift.iteritems():
            if val[0]['Staff Type'] != staff: continue
            #iterate over the shifts
            for s in val:
                tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
                fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                if s['Clock-Out'] == "\"\"":
                    to =  datetime.now()
                else:
                    to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                if  fr <= tran and tran <= to:
                    report[name]['tips'] += (float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]) / worked
                
emails={}
for e in result['data']:
    if e['user']['email'] == '': continue
    emails[e['user']['firstname'].lower()] = e['user']['email']

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import time
ts = time.gmtime()
 
fromaddr = "tycscmanager@gmal.com"
toaddr = "tycscreports@gmail.com"
 
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login("tycscreports@gmail.com", sys.argv[1])

for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
    if k.lower() not in emails.keys(): continue
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    #toaddr = emails[k.lower()]
    #msg['To'] = toaddr
    msg['To'] = toaddr
    msg['Subject'] = "[Yellow Chilli] Earning for " + time.strftime("%c", ts)
    body = "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10} {:<10}  {:<10} \n".format('Name','Type', 'Hours','Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
    body += "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10} {:<10}  {:<10} ".format(k, v['type'], v['hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    print "Sending mail to " + k + " at " + emails[k.lower()]
server.quit()

print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10} {:<10}  {:<10} ".format('Name','Type', 'Hours','Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
hours, pay, tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0
for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
    print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10} {:<10}  {:<10} ".format(k, v['type'], v['hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
    hours += v['hours']
    pay += v['pay']
    tips += v['tips']
    extra_tips += v['extra-tips']
    cash += v['cash']
    
print "{:<30} {:<15} {:<10} {:<10} {:<10}  {:<10} {:<10}  {:<10} ".format("Total", "", hours, pay, tips, extra_tips, cash, hours+pay+tips+extra_tips-cash)
