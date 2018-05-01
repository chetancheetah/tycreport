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

date = ""
#read the shift details and the bills
with open(sys.argv[2]) as f:
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

#how to share
shared_tips= {
    'Kitchen'  : 0.08,   #  8%
    'Busser' : 0.10,     # 10%
    'Food Runner' : 0.05,#  5%
    'Hostess' : 0.02,    #  2%
    'Bartender': 0.05,   #  5%
}

report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}

for u in shift.keys(): report[u] = {'type':shift[u][0]['Staff Type'],'hours':0.0, 'ot-hours':0.0, 'pay': 0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}

for name, shifts in shift.iteritems():
    report[name]['shifts'] = shifts
    dat = '0'
    old = {'hours':0.0}
    hours = 0.0
    for s in shifts:
        s['hours'] = 0.0
        ndate = s['Clock-In'].split(' ')[0].split('-')[2]
        if dat != ndate:
            old['hours'] = hours
            hours = 0.0
            dat  = ndate
        hours += float(s['Duration'])
        old = s
    old['hours'] = hours
    for s in shifts:
        hours = s['hours'] if s['hours'] <= 8.0 else 8.0
        ot_hours = 0.0 if s['hours'] <= 8.0 else (s['hours'] - 8.0)
        report[name]['hours'] += hours
        report[name]['ot-hours'] += ot_hours
        rate = float(s['Hourly Rate'][1:])
        report[name]['pay'] += hours * rate + ot_hours*1.5*rate
# go over all the shift details
for t in trans:
    if t['Staff'] not in report.keys() :
        report['Kitchen']['tips'] += float(t['Tip'][1:])*0.7 + float(t['Gratuity'][1:])*0.7
    else:
        report[t['Staff']]['tips'] += float(t['Tip'][1:])*0.7 + float(t['Gratuity'][1:])*0.7
    if t['Name'] == 'Cash':
        report[t['Staff'] if t['Staff'] in report.keys() else 'Kitchen']['cash'] += float(t['Payment Amount'][1:])

    #distribute the tips amongst the helpers
    for staff in shared_tips.keys():
        worked = 0
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] != staff: continue
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
                report[t['Staff'] if t['Staff'] in report.keys() else 'Kitchen']['extra-tips'] += float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]
            else:
                report['Kitchen']['tips'] += float(t['Tip'][1:])*shared_tips[staff] + float(t['Gratuity'][1:])*shared_tips[staff]
            continue
#            print "No one worked as " + staff + " for bill " + t['Bill Number'] + " at " + t['Bill Date']
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] != staff: continue
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
    if k.lower() not in emails.keys():
        print "Need email for " + k
        continue
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    if sys.argv[3] == 'no':
        #toaddr = emails[k.lower()]
    #else:
        break
    msg['To'] = toaddr
    msg['Subject'] = "[Yellow Chilli] Earning from %s/%s to %s/%s" % (date[4], date[5], date[7], date[8])
    body = "Shift Details\n\n"
    body += "{:>30} {:>15} {:>14} {:>15} {:>14}  {:>15}(hours) {:>14}\n".format('Name','Staff Type', 'Clock-In', 'Clock-Out', 'hours', 'Hourly Rate', 'Pay')
    for s in v['shifts']:
        body += "{:>30} {:>15} {:>14} {:>15} {:>14}hours  {:>15} {:>14}\n".format(k, s['Staff Type'], s['Clock-In'], s['Clock-Out'], s['Duration'], s['Hourly Rate'], s['Pay'])
    body += "\n\nPay Details\n\n"
    body += "{:>30} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} {:>15} \n".format('Name','Type', 'Hours', 'OT-Hours','Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
    body += "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} \n".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
    body += "\n\nPaycheck will be run every two weeks and checks will be given on Tuesday \n Regards TYC"
    body += "\n\nEvery server keeps his tips and gives\n (10% - busser, 5% food runner, 8% kitchen, 5% bartender, 2% host),\n If there is no busser or food runner and server has to bus and run the food and he will keep that share with himself (shown in extra-tips)\n\n\n Please contact the Manager if there is any issue with the calculation\n"
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    print "Sending mail to " + k + " at " + emails[k.lower()]
server.quit()

print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} ".format('Name','Type', 'Hours', 'OT-hours', 'Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
hours, ot_hours, pay, tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
    print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} ".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
    hours += v['hours']
    ot_hours += v['ot-hours']
    pay += v['pay']
    tips += v['tips']
    extra_tips += v['extra-tips']
    cash += v['cash']
    
print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} ".format("Total", "", hours, ot_hours, pay, tips, extra_tips, cash, pay+tips+extra_tips-cash)
