import sys
import csv
from datetime import datetime
import operator
import subprocess
import json

def dollartofloat(s):
    if '$' not in s: return s
    if s[0] == '"':
        s = s[1:-1]
    if s[0] == '-':
        return -float(s.split('$')[1])
    return float(s.split('$')[1])

need_user = None

if len(sys.argv) == 4:
    need_user = sys.argv[3]

result = subprocess.check_output(['curl', 'https://api.7shifts.com/v1/users',  '-u', 'VS5RDPW86QD5X2A6D2YZT56VM9CLE3D8:'])
result = json.loads(result)

shift = {'Kitchen' : [
    {'Name' : 'Kitchen',
     'Staff Type' : 'Kitchen',
     'Clock-In' : '2000-01-01 00:00',
     'Clock-Out': '2100-01-01 00:00',
     'Duration' : '0.0',
     'Hourly Rate' : 0.0,
     'Pay' : '0.0',
 } ]}
ignore_list = ["4103", "6850"]
trans = []
orders = {}
date = ""
#read the shift details and the bills
with open(sys.argv[2]) as f:
    rows = f.readlines()
s = 0
for row in rows:
    row = row.replace('\n','')
    row = row.replace('\r','')
    if 'theyellow' in row:
        if s: date = row
        continue
    if 'Name' in row:
        keys = row.split(',')
        continue
    if 'REPORT' in row:
        s = 1
        continue
    # handle the amount > 1000
    if '"$' in row:
        nrow = ""
        amount = False
        for c in row:
            if c == '$' :
                amount = True
            if c == '.':
                amount = False
            if c == ',' and amount:
                continue
            nrow += c
        row = nrow
    row = row.replace('Admin', 'Kitchen')
    cols = row.split(',')
    cols1 = {}
    i = 0
    for col in cols:
        cols1[keys[i]] = dollartofloat(col)
        i += 1
    if s:
        if cols1['Staff Type'] == 'Owner': continue
        if cols1['Staff Type'] == 'Bar back':
            cols1['Staff Type'] = 'Bartender'
        if shift.has_key(cols1['Name']):
            shift[cols1['Name']].append(cols1)
        else:
            shift[cols1['Name']] = [cols1]
    else:
        if cols1['Order Number'] in ignore_list:
            print "Ignoring " + cols1['Order Number']
            continue
        # gratuity is duped in all the partial payments so remove it
        if cols1['Order Number'] in orders.keys() and cols1['Type'] == 'Partial Payment':
            cols1['Gratuity'] = 0.0
        orders[cols1['Order Number']] = True
        trans.append(cols1)

date = date.split('-')

#how to share
shared_tips= {
    'Kitchen'  : 0.08,   #  8%
    'Busser' : 0.15,     # 15%
    'Food Runner' : 0.05,#  5%
    'Hostess' : 0.02,    #  2%
    'Bartender': 0.05,   #  5%
}


report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'buffet-tips':0.0,'extra-tips':0.0, 'cash':0.0}}

for u in shift.keys(): report[u] = {'type':shift[u][0]['Staff Type'],'hours':0.0, 'ot-hours':0.0, 'pay': 0.0, 'tips':0.0, 'buffet-tips':0.0, 'extra-tips':0.0, 'cash':0.0, 'total':0.0, 'worked' : 0 }

for name, shifts in shift.iteritems():
    report[name]['shifts'] = shifts
    dat = '0'
    old = {'hours':0.0}
    hours = 0.0
    for s in shifts:
        s['tips'] = 0.0
        s['buffet-tips'] = 0.0
        s['extra-tips'] = 0.0
        s['hours'] = 0.0
        s['total'] = 0.0
        s['worked'] = 0
        for t in shared_tips.keys():
            s[t] =0
        ndate = s['Clock-In'].split(' ')[0].split('-')[2]
        if dat != ndate:
            old['hours'] = hours
            hours = 0.0
            dat  = ndate
        hours += float(s['Duration'])
        old = s
        s['fr'] = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
        if s['Clock-Out'] == "\"\"":
            to = datetime.now()
        else:
            to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
        s['to'] = to
    old['hours'] = hours
    for s in shifts:
        hours = s['hours'] if s['hours'] <= 8.0 else 8.0
        ot_hours = 0.0 if s['hours'] <= 8.0 else (s['hours'] - 8.0)
        report[name]['hours'] += hours
        report[name]['ot-hours'] += ot_hours
        rate = s['Hourly Rate']
        report[name]['pay'] += hours * rate + ot_hours*1.5*rate

# go over all the shift details
total_tips = 0.0
for t in trans:
    tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')

    total_tips += t['Tip'] + t['Gratuity']

    #figure out if its buffet
    if t['Name'] == 'Cash':
        report[t['Staff'] if t['Staff'] in report.keys() else 'Kitchen']['cash'] += t['Payment Amount'] - t['Change']

    if (tran.year >= 2019 and tran.month >= 4 and tran.hour <= 16 and tran.strftime("%A") == 'Sunday' and
        (tran.year == 2019 and tran.month != 5 and tran.day != 12)):
        report['Kitchen']['buffet-tips'] += (t['Tip'])*shared_tips['Kitchen'] + (t['Gratuity'])*shared_tips['Kitchen']
        worked = 0
        for  name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] == 'Manager' or s['Staff Type'] == 'Kitchen' : continue
                fr = s['fr']
                to = s['to']
                if  fr <= tran and tran <= to:
                    worked += 1
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] == 'Manager' or s['Staff Type'] == 'Kitchen' : continue
                fr = s['fr']
                to = s['to']
                if  fr <= tran and tran <= to:
                    s['buffet-tips'] += (t['Tip']*0.92 + t['Gratuity']*0.92)/worked
                    s['worked'] = worked
                    report[name]['buffet-tips'] +=  (t['Tip']*0.92 + t['Gratuity']*0.92)/worked
        continue
    if t['Staff'] not in report.keys() :
        report['Kitchen']['tips'] += t['Tip']*0.65 + t['Gratuity']*0.65
    else:
        report[t['Staff']]['tips'] += t['Tip']*0.65 + t['Gratuity']*0.65

    once = True
    #distribute the tips amongst the helpers
    for staff in shared_tips.keys():
        worked = 0
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] != staff: continue
                fr = s['fr']
                to = s['to']
                if  fr <= tran and tran <= to:
                    worked += 1
        # relax the check a little
        if worked == 0:
            for name, val in shift.iteritems():
                #iterate over the shifts
                for s in val:
                    if s['Staff Type'] != staff: continue
                    fr = s['fr']
                    to = s['to']
                    if  fr.year == tran.year and fr.month == tran.month and fr.day == tran.day:
                        if (fr.hour < 16 and to.hour < 16 and tran.hour < 16) or (fr.hour >= 16 and to.hour >= 16 and tran.hour >= 16):
                            worked += 1
        if worked == 0:
            # if there was no busser  or food runner then assumption the server would have bussed
            if staff == 'Busser' or staff == 'Food Runner':
                report[t['Staff'] if t['Staff'] in report.keys() else 'Kitchen']['extra-tips'] += (t['Tip'])*shared_tips[staff] + (t['Gratuity'])*shared_tips[staff]
            else:
                report['Kitchen']['tips'] += (t['Tip'])*shared_tips[staff] + (t['Gratuity'])*shared_tips[staff]
#            continue
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                fr = s['fr']
                to = s['to']
                # if its his own then need to update shift tips.
                if s['Name'] == t['Staff']:
                    if  fr <= tran and tran <= to:
                        if once:
                            s['tips'] += t['Tip']*0.65 + t['Gratuity']*0.65
                            once = False
                        if worked == 0 and (staff == 'Busser' or staff == 'Food Runner'):
                            s['extra-tips'] += ((t['Tip'])*shared_tips[staff] + (t['Gratuity'])*shared_tips[staff])
                        if s[staff] == 0:
                            s[staff] = worked
                if s['Staff Type'] != staff: continue
                if  fr <= tran and tran <= to:
                    report[name]['tips'] += ((t['Tip'])*shared_tips[staff] + (t['Gratuity'])*shared_tips[staff]) / worked
                    s['tips'] += ((t['Tip'])*shared_tips[staff] + (t['Gratuity'])*shared_tips[staff]) / worked
                    if s['worked'] == 0:
                        s['worked'] = worked
                    s['total'] += t['Tip'] + t['Gratuity']

print "Total tips %f"%total_tips
                
emails={}
for e in result['data']:
    if e['user']['email'] == '':
        print "Need email for " + e['user']['firstname']
        continue
    print "Email for " + e['user']['firstname'] + " is " +  e['user']['email']
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
#    if k.lower() not in emails.keys():
#        print "Need email for " + k
#        continue
#   toaddr = emails[k.lower()]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
#    if need_user is None:
#        break
    if need_user and (need_user != k and need_user != 'yes'):
        continue
    msg['To'] = toaddr
    msg['Subject'] = "[Yellow Chilli] %s  Earning from %s/%s to %s/%s" % (k, date[4], date[5], date[7], date[8])
    body = "Shift Details\n\n"
    if v['shifts'][0]['Staff Type'] == 'Server':
        body += "{:>20} {:>10} {:>18} {:>18} {:>14} {:>15} {:>14}  {:>14}  {:>14} {:>14} {:>14} {:>14}\n".format('Name','Staff Type', 'Clock-In', 'Clock-Out', 'hours', 'Hourly Rate', 'Pay', 'Tips', 'buffet-tips', 'extra-tips', 'Busser', 'Food Runner')
        for s in v['shifts']:
            body += "{:>20} {:>10} {:>18} {:>18} {:>14} {:>15} {:>14.2f}$ {:>14.2f}$ {:>14.2f}$ {:>14.2f}$ {:>14} {:>14}\n".format(k, s['Staff Type'], s['Clock-In'], s['Clock-Out'], s['Duration'], s['Hourly Rate'], s['Pay'], s['tips'], s['buffet-tips'], s['extra-tips'], s['Busser'], s['Food Runner'])
    else:
        body += "{:>20} {:>10} {:>18} {:>18} {:>14} {:>15} {:>14} {:>14} {:>14}  {:>14}\n".format('Name','Staff Type', 'Clock-In', 'Clock-Out', 'hours', 'Hourly Rate', 'Pay', 'Tips', 'buffet-tips', v['type']+"\'s")
        for s in v['shifts']:
            body += "{:>20} {:>10} {:>18} {:>18} {:>14} {:>15} {:>14.2f}$ {:>14.2f}$ {:>14}\n".format(k, s['Staff Type'], s['Clock-In'], s['Clock-Out'], s['Duration'], s['Hourly Rate'], s['Pay'], s['tips'], s['buffet-tips'], s['worked'])
    body += "\n\nPay Details\n\n"
    body += "{:>30} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} {:>15} \n".format('Name','Type', 'Hours', 'OT-Hours','Pay', 'tips', 'buffet-tips', 'extra-tips', 'cash-advance', 'Total')
    body += "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} \n".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['buffet-tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['buffet-tips'] + v['extra-tips'] - v['cash'])
    body += "\n\nPaycheck will be run every two weeks and checks will be given on Tuesday \n Regards TYC"
    body += "\n\nEvery server keeps his tips and gives\n (15% - busser, 5% food runner, 8% Expeditor, 5% bartender, 2% host),\n Extra tips when there is no busser or food runner during that shift\n\n\n Please contact the Manager if there is any issue with the calculation\n"
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    print "Sending mail to " + k + " at " + toaddr
server.quit()

print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15}  {:>15} ".format('Name','Type', 'Hours', 'OT-hours', 'Pay', 'tips', 'buffet-tips', 'extra-tips', 'cash-advance', 'Total')
hours, ot_hours, pay, tips, buffet_tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
#for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
for k, v in sorted(report.items()):
    print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15} {:>15}  {:>15} ".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['buffet-tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['buffet-tips'] + v['extra-tips'] - v['cash'])
    hours += v['hours']
    ot_hours += v['ot-hours']
    pay += v['pay']
    tips += v['tips']
    buffet_tips += v['buffet-tips']
    extra_tips += v['extra-tips']
    cash += v['cash']
    
print "{:>30} {:>15} {:>15} {:>15} {:>15} {:>15}  {:>15} {:>15} {:>15} {:>15} ".format("Total", "", hours, ot_hours, pay, tips, buffet_tips, extra_tips, cash, pay+tips+buffet_tips+extra_tips-cash)
