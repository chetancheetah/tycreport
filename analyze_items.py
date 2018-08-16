import sys
import csv
import os
import fnmatch
from datetime import datetime

input_dir = sys.argv[1]

report = {}
weeks = {}
for root, _, filenames in os.walk(input_dir):
    for filename in fnmatch.filter(filenames, "*.csv"):
        fname = os.path.join(root, filename)
        with open(fname, 'r') as f:
            rows = f.readlines()
        for row in rows:
            if 'theyellow' in row:
                date = row.split('-')
                week="%s/%s - %s/%s"%(date[3], date[4], date[6], date[7])
                weeks[week] = 1
                continue
            if 'Menu Item' in row: continue
            if 'REPORT SUMMARY' in row: continue
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
            cols = row.split(',')
            if cols[0] not in report.keys():
                report[cols[0]] = {}
            report[cols[0]][week] = float(cols[3]) + float(cols[5])

for i in report.keys():
    s = i + ","
    for w in weeks:
        if w not in report[i].keys():
            s += ','
        else:
            s += str(report[i][w]) + ','
    print s

