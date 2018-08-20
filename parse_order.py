import sys
import subprocess
import pprint
import BeautifulSoup

result = subprocess.check_output(['pdf2txt.py', sys.argv[1]])

file = open('tmp.txt', 'w')
file.write(result)
file.close()

report = {}

with open('tmp.txt') as f:
    orows = f.readlines()

report['items'] = []

ignore_list=['Price',
             '$',
             'Qty.',
             'Page',
             'Special instructions',
             'doordash.com',
             'For any urgent',
             'Total:',
             'Commission will be',
             '~ End of Order ~',
             'Tax',
             'Set special hours',
             'please visit']
rows = []
for row in orows:
    row = row.strip()
    if row == '':continue
    ignore = 0
    for i in ignore_list:
        if i in row:
            ignore = 1
    if ignore: continue
    rows.append(row)        

print rows

i =0
for row in rows:
    if 'Customer:' in row:
        report['customer'] = row.split(':')[1].strip()
    if 'Order scheduled for' in row:
        report['pickup'] = row.split('for')[1].strip()
    if 'Delivery #' in row:
        report['delivery'] = row.split('#')[1].strip()
    if report['customer'] == row:
        report['phone'] = rows[i+1].strip()
    i+=1

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(report)
