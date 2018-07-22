import sys
import csv
from datetime import datetime

def dollartofloat(s):
    if '$' not in s: return s
    if s[0] == '"':
        s = s[1:-1]
    if s[0] == '-':
        return -float(s.split('$')[1])
    return float(s.split('$')[1])


shift = {}
trans = []
orders = {}

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
        if shift.has_key(cols1['Name']):
            shift[cols1['Name']].append(cols1)
        else:
            shift[cols1['Name']] = [cols1]
    else:
        # gratuity is duped in all the partial payments so remove it
        if cols1['Order Number'] in orders.keys() and cols1['Type'] == 'Partial Payment':
            cols1['Gratuity'] = 0.0
        orders[cols1['Order Number']] = True
        trans.append(cols1)

date = date.split('-')
total=8
lunch=9
dinner=10
days = ['Total', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
report = {}
dt="%s-%s-%s"%(date[3], date[4], date[5])
from_rep = datetime.strptime(dt, '%Y-%m-%d')
dt="%s-%s-%s"%(date[6], date[7], date[8])
to_rep = datetime.strptime(dt, '%Y-%m-%d')
fw = from_rep.isocalendar()[1]
tw = to_rep.isocalendar()[1]
for d in days:
    report[d] = {}
    for w in range(fw,tw+1):
        report[d][w] = {}
        for h in range(8,24):
            report[d][w][h] = {
                'sales'      : 0.0,
                'labor'      : 0.0,
                'orders'     : 0,
#                'seats'      : 0,
                'Server'     : 0,
                'Bartender'  : 0,
                'Busser'     : 0,
                'Hostess'    : 0,
                'Food Runner': 0,
            }
tot = "Total"
for i in shift:
    for s in shift[i]:
        fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
        if s['Clock-Out'] == "\"\"":
            to = datetime.now()
        else:
            to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
        wd = fr.strftime("%A")
        week = fr.isocalendar()[1]
        t = s['Staff Type']
        if t not in report[wd][week][fr.hour].keys(): continue
        report[wd][week][8][t] += 1
        report[tot][week][8][t] += 1
        pay = s['Pay']
        report[wd][week][8]['labor'] += pay
        report[tot][week][8]['labor'] += pay
        if to.hour < 18:
            report[wd][week][9][t] += 1
            report[wd][week][9]['labor'] += pay
            report[tot][week][9][t] += 1
            report[tot][week][9]['labor'] += pay
        else:
            report[wd][week][10][t] += 1
            report[wd][week][10]['labor'] += pay
            report[tot][week][10][t] += 1
            report[tot][week][10]['labor'] += pay
        for i in range(fr.hour, to.hour+1):
            report[wd][week][i][t] += 1
            report[tot][week][i][t] += 1
            report[wd][week][i]['labor'] += s['Hourly Rate']
            report[tot][week][i]['labor'] += s['Hourly Rate']

for t in trans:
    tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
    wd = tran.strftime("%A")
    week = tran.isocalendar()[1]
    amt = (t['Applied to Bill'] - t['Gratuity'])/1.09
    report[wd][week][8]['sales'] += amt
    report[tot][week][8]['sales'] += amt
    if tran.hour < 18:
        report[wd][week][9]['sales'] += amt
        report[tot][week][9]['sales'] += amt
    else:
        report[wd][week][10]['sales'] += amt
        report[tot][week][10]['sales'] += amt
    report[wd][week][tran.hour]['sales'] += amt
    report[tot][week][tran.hour]['sales'] += amt
    report[tot][week][tran.hour]['orders'] += 1
    report[wd][week][tran.hour]['orders'] += 1


#shift time
st = {
    'Monday'   : [11, 30, 14, 30, 17, 00, 22, 00],
    'Tuesday'  : [11, 30, 14, 30, 17, 00, 22, 00],
    'Wednesday': [11, 30, 14, 30, 17, 00, 22, 00],
    'Thursday' : [11, 30, 14, 30, 17, 00, 22, 00],
    'Friday'   : [11, 30, 14, 30, 17, 00, 22, 30],
    'Saturday' : [12, 00, 15, 00, 17, 30, 22, 30],
    'Sunday'   : [12, 00, 15, 00, 17, 30, 22, 00],
    }


types = {}
for i in shift:
    for s in shift[i]:
        types[s['Staff Type']] = 1
        break

start_day = from_rep.timetuple().tm_yday
end_day = to_rep.timetuple().tm_yday
rows = ""
compare = ""
for d in range(start_day, end_day+1):
    total = 0.0
    morn = 0.0
    even = 0.0
    once = ""
    staff_row = ""
    for t in types.keys():
        for i in shift:
            for s in shift[i]:
                if t != s['Staff Type']: continue
                fr1 = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                if fr1.timetuple().tm_yday != d: continue
                fr = fr1
                week = fr.isocalendar()[1]
                if once == "":
                    once = "done"
                    decl_row ="var rows_%d_%d_%d = [\n"%(fr.year, fr.month, fr.day)
                    compare += "if (date_selected == \"%d-%02d-%02d\") dataTable.addRows(rows_%d_%d_%d);\n"%(fr.year, fr.month, fr.day, fr.year, fr.month, fr.day)
                total += s['Pay']
                to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                wd = fr.strftime("%A")
                if fr.hour < st[wd][2]:
                    morn += s['Pay']
                else:
                    even += s['Pay']
                staff_row += "          [ '%s-%s', '$%.2f@$%.2f', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
                    s['Staff Type'],s['Name'], s['Pay'], s['Hourly Rate'],
                    fr.year, fr.month, fr.day, fr.hour, fr.minute, fr.second,
                    to.year, to.month, to.day, to.hour, to.minute, to.second)
    hour_row = ""
    for h in range(11,24):
        orders = report[wd][week][h]['orders'] if report[wd][week][h]['orders'] else 1
        sales = report[wd][week][h]['sales'] if report[wd][week][h]['sales'] else 1.0
        if sales == 1.0: continue
        hour_row += "          [ 'Hourly', '$%.2f/%d Tables/%d covers', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            sales, orders, (sales/28),
            fr.year, fr.month, fr.day, h, 0, 0,
            to.year, to.month, to.day, h+1, 0, 0)

    morn_sales = report[wd][week][9]['sales'] if report[wd][week][9]['sales'] else 1.0
    even_sales = report[wd][week][10]['sales'] if report[wd][week][10]['sales'] else 1.0
    day_sales = report[wd][week][8]['sales'] if report[wd][week][8]['sales'] else 1.0
    shift_row = "          [ 'Shift', 'Sales $%.2f Labor $%.2f = %0.2f%%', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
        morn_sales, morn, morn/morn_sales*100.0,
        fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
        to.year, to.month, to.day, st[wd][2], st[wd][3], 0)
    shift_row += "          [ 'Shift', 'Sales $%.2f Labor $%.2f = %0.2f%%', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
        even_sales, even, even/even_sales*100.0,
        fr.year, fr.month, fr.day, st[wd][4], st[wd][5], 0,
        to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
    day_row = "          [ '%s', 'Sales $%.2f Labor $%.2f = %0.2f%%', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
        wd,
        day_sales, total, total/day_sales*100.0,
        fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
        to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
    end_row = "];\n"

    rows += "%s%s%s%s%s%s"%(decl_row, day_row, shift_row, hour_row, staff_row, end_row)
header="""
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
  google.charts.load('current', {'packages':['timeline']});
  google.charts.setOnLoadCallback(drawChart);
  %s
  function drawChart() {
      var container = document.getElementById('timeline');
      var chart = new google.visualization.Timeline(container);
      var dataTable = new google.visualization.DataTable();
      var date_selected = document.getElementById("sel_date").value;
      dataTable.addColumn({ type: 'string', id: 'Name' });
      dataTable.addColumn({ type: 'string', id: 'Pay' });
      dataTable.addColumn({ type: 'date', id: 'Start' });
      dataTable.addColumn({ type: 'date', id: 'End' });
      %s
      var options = {'title':'FOH Labor graph',
                     'width':1400,
                     'height':700};
     chart.draw(dataTable);
  }
  function date_left() {
     document.getElementById("sel_date").stepDown(1);
     date_changed();
  }
  function date_right() {
     document.getElementById("sel_date").stepUp(1);
     date_changed();
  }
  function date_changed() {
     drawChart()
  }
</script>

<div id="timeline" style="height:700;width:1400"></div>
<center><button type="button" onclick="date_left()" > < </button>
<input type="date" id="sel_date" name="trip"
               value="%d-%02d-%02d"
               min="%d-%02d-%02d" max="%d-%02d-%02d" 
               onchange="date_changed(event);" / >
<button type="button" onclick="date_right()" > > </button>
</center>
""" % (rows, compare,
       to_rep.year, to_rep.month, to_rep.day,
       from_rep.year, from_rep.month, from_rep.day,
       to_rep.year, to_rep.month, to_rep.day)
print header
