import sys
import csv
import copy
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
s = 0
for row in rows:
    row = row.replace('\n','')
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
dt="%s-%s-%s"%(date[3], date[4], date[5])
from_rep = datetime.strptime(dt, '%Y-%m-%d')
dt="%s-%s-%s"%(date[6], date[7], date[8])
to_rep = datetime.strptime(dt, '%Y-%m-%d')
fy = from_rep.year
ty = to_rep.year

day='day'
week='week'
month='month'
report='report'
sales='sales'
labor='labor'
tips='tips'
orders='orders'
rep= {
    sales      : 1.0,
    labor      : 0.0,
    tips       : 0.0,
    orders     : 0,
    }
records = {}
for y in range(fy, ty+1):
    records[y] = {
        report : copy.deepcopy(rep),
        month  : {},
        week   : {},
        day    : {},
        }
    #init months
    sm = 1 if y != fy else from_rep.timetuple().tm_mon
    em = (12 if y != ty else to_rep.timetuple().tm_mon)+ 1
    for m in range(sm, em) :
        records[y][month][m] = { report: copy.deepcopy(rep) }

    #init weeks
    sw = 1 if y != fy else from_rep.isocalendar()[1]
    ew = (52 if y != ty else to_rep.isocalendar()[1]) + 1
    for w in range(sw, ew):
        records[y][week][w] = { report: copy.deepcopy(rep) }

    #init days
    sd = 1 if y != fy else from_rep.timetuple().tm_yday
    ed = (365 if y != ty else to_rep.timetuple().tm_yday) + 1
    for d in range(sd, ed):
        records[y][day][d] = {
            'shifts' : {},
            'trans' : [],
            report:{},
            }
        for h in range(7,24):
            records[y][day][d][report][h] = copy.deepcopy(rep)

for i in shift:
    for s in shift[i]:
        fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
        if s['Clock-Out'] == "\"\"":
            to = datetime.now()
            s['Clock-Out'] = '%d-%d-%d %d:%d'%(to.year, to.month, to.day, to.hour, to.minute)
        else:
            to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
        yr = fr.year
        yd = fr.timetuple().tm_yday
        t = s['Staff Type'] + '-'
        ti = t+i
        if yd not in records[yr][day]:
            continue
        if ti not in records[yr][day][yd]['shifts'].keys():
            records[yr][day][yd]['shifts'][ti] = []
        records[yr][day][yd]['shifts'][ti].append(s)
for t in trans:
    tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
    yr = tran.year
    yd = tran.timetuple().tm_yday
    records[yr][day][yd]['trans'].append(t)

avg = {
    'Monday'   : copy.deepcopy(rep),
    'Tuesday'  : copy.deepcopy(rep),
    'Wednesday': copy.deepcopy(rep),
    'Thursday' : copy.deepcopy(rep),
    'Friday'   : copy.deepcopy(rep),
    'Saturday' : copy.deepcopy(rep),
    'Sunday'   : copy.deepcopy(rep),
    }

total=7
lunch=8
dinner=9
# go thru all the shifts and calculate total, per session, per hour labor costs and averages too.
for y in sorted(records.keys()):
    for d in sorted(records[y][day].keys()):
        for e in records[y][day][d]['shifts'].keys():
            for s in records[y][day][d]['shifts'][e]:
                fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                for h in range(fr.hour, to.hour+1):
                    if h not in records[y][day][d][report].keys():
                        continue
                    records[y][day][d][report][h][labor] += s['Hourly Rate']
                records[y][day][d][report][total][labor] += s['Pay']
                if to.hour < 18:
                    records[y][day][d][report][lunch][labor] += s['Pay']
                else:
                    records[y][day][d][report][dinner][labor] += s['Pay']
                records[y][month][fr.month][report][labor] += s['Pay']
                records[fr.isocalendar()[0]][week][fr.isocalendar()[1]][report][labor] += s['Pay']
                records[y][report][labor] += s['Pay']
                avg[fr.strftime("%A")][labor] += s['Pay']
        for t in records[y][day][d]['trans']:
            tran = datetime.strptime(t['Bill Date'], '%Y-%m-%d %H:%M')
            amt = (t['Applied to Bill'] - t['Gratuity'])/1.09
            tip = t['Tip'] + t['Gratuity']
            records[y][day][d][report][tran.hour][sales] += amt
            records[y][day][d][report][tran.hour][tips] += tip
            records[y][day][d][report][tran.hour][orders] += 1
            if tran.hour < 18:
                records[y][day][d][report][lunch][sales] += amt
                records[y][day][d][report][lunch][tips] += tip
                records[y][day][d][report][lunch][orders] += 1
            else:
                records[y][day][d][report][dinner][sales] += amt
                records[y][day][d][report][dinner][tips] += tip
                records[y][day][d][report][dinner][orders] += 1
            records[y][day][d][report][total][sales] += amt
            records[y][day][d][report][total][tips] += tip
            records[y][day][d][report][total][orders] += 1
            records[y][report][sales] += amt
            records[fr.isocalendar()[0]][week][fr.isocalendar()[1]][report][sales] += amt
            records[y][month][fr.month][report][sales] += amt
            avg[fr.strftime("%A")][sales]  += amt
            avg[fr.strftime("%A")][tips]   += tip
        avg[fr.strftime("%A")][orders] += 1

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

def _d(d):
    return '${:,.2f}'.format(d)

rows = ""
compare = ""
#now generate the script
for y in sorted(records.keys()):
    for d in sorted(records[y][day].keys()):
        wd = ""
        once = ""
        staff_row = ""
        for e in sorted(records[y][day][d]['shifts'].keys()):
            for s in records[y][day][d]['shifts'][e]:
                fr = datetime.strptime(s['Clock-In'], '%Y-%m-%d %H:%M')
                to = datetime.strptime(s['Clock-Out'], '%Y-%m-%d %H:%M')
                if once == "":
                    once = "done"
                    wd = fr.strftime("%A")
                    decl_row ="var rows_%d_%d_%d = [\n"%(fr.year, fr.month, fr.day)
                    compare += "if (date_selected == \"%d-%02d-%02d\") dataTable.addRows(rows_%d_%d_%d);\n"%(fr.year, fr.month, fr.day, fr.year, fr.month, fr.day)
                staff_row += "          [ '%s-%s', '$%s@$%.2f', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
                    s['Staff Type'],s['Name'], '{:,}'.format(s['Pay']), s['Hourly Rate'],
                    fr.year, fr.month, fr.day, fr.hour, fr.minute, fr.second,
                    to.year, to.month, to.day, to.hour, to.minute, to.second)
        hour_row = ""
        for h in range(11,24):
            order = records[y][day][d][report][h][orders]
            sale = records[y][day][d][report][h][sales]
            tip = records[y][day][d][report][h][tips]
            if sale == 1.0:
                hour_row += "          [ 'Hourly', '$%.2f', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
                    0.0,
                    fr.year, fr.month, fr.day, h, 0, 0,
                    to.year, to.month, to.day, h+1, 0, 0)
                continue
            hour_row += "          [ 'Hourly', '$%.2f/%d Tables/%d covers Tips$%.2f', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
                sale, order, (sale/28), tip,
                fr.year, fr.month, fr.day, h, 0, 0,
                to.year, to.month, to.day, h+1, 0, 0)

        morn_sales = records[y][day][d][report][lunch][sales] 
        even_sales = records[y][day][d][report][dinner][sales] 
        day_sales  = records[y][day][d][report][total][sales] 
        day_avg_sales = avg[wd][sales]/avg[wd][orders]
        morn_tips  = records[y][day][d][report][lunch][tips] 
        even_tips  = records[y][day][d][report][dinner][tips] 
        day_tips   = records[y][day][d][report][total][tips] 
        day_avg_tips = avg[wd][tips]/avg[wd][orders]
        morn_labor = records[y][day][d][report][lunch][labor] 
        even_labor = records[y][day][d][report][dinner][labor] 
        day_labor  = records[y][day][d][report][total][labor] 
        day_avg_labor = avg[wd][labor]/avg[wd][orders]
        shift_row  = "          [ 'Shift', 'Sle %s Lbr %s(%0.2f%%) Tip $%.2f(%0.2f%%)', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            _d(morn_sales), _d(morn_labor), morn_labor/morn_sales*100.0,
            morn_tips, morn_tips/morn_sales*100.00,
            fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
            to.year, to.month, to.day, st[wd][2], st[wd][3], 0)
        shift_row += "          [ 'Shift', 'Sle %s Lbr %s(%0.2f%%) Tip $%.2f(%0.2f%%)', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            _d(even_sales), _d(even_labor), even_labor/even_sales*100.0,
            even_tips, even_tips/even_sales*100.00,
            fr.year, fr.month, fr.day, st[wd][4], st[wd][5], 0,
            to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
        day_row = "          [ '%s', 'Sle %s Lbr %s(%0.2f%%) Tip $%.2f(%0.2f%%)', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            wd,
            _d(day_sales), _d(day_labor), day_labor/day_sales*100.0,
            day_tips, day_tips/day_sales*100.00,
            fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
            to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
        day_avg_row = "          [ '%s-AVG', 'Sle %s Lbr %s(%0.2f%%) Tip $%.2f(%0.2f%%)', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            wd,
            _d(day_avg_sales), _d(day_avg_labor), day_avg_labor/day_avg_sales*100.0,
            day_avg_tips, day_avg_tips/day_avg_sales*100.00,
            fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
            to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
        stat_row = "          [ 'Total', '%d=Sale %s/ lbr %s %s=Sale %s/ lbr %s Week-%d=Sale %s/ lbr %s', new Date(%d,%d,%d,%d,%d,%d), new Date(%d,%d,%d,%d,%d,%d) ],\n"%(
            y, _d(records[y][report][sales]), _d(records[y][report][labor]),
            fr.strftime("%b"),_d(records[y][month][fr.month][report][sales]),_d(records[y][month][fr.month][report][labor]),
            fr.isocalendar()[1],
            _d(records[fr.isocalendar()[0]][week][fr.isocalendar()[1]][report][sales]),
            _d(records[fr.isocalendar()[0]][week][fr.isocalendar()[1]][report][labor]),
            fr.year, fr.month, fr.day, st[wd][0], st[wd][1], 0,
            to.year, to.month, to.day, st[wd][6], st[wd][7], 0)
        end_row = "];\n"
        rows += "%s%s%s%s%s%s%s%s"%(decl_row, stat_row, day_row, day_avg_row, shift_row, hour_row,  staff_row, end_row)

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
