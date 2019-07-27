import email
import getpass, imaplib
import os
import sys
from datetime import datetime
import mysql.connector



userName = sys.argv[1]
passwd = sys.argv[2]
port = sys.argv[3]

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user=userName,
    passwd=passwd,
    database=userName,
    port=port,
)

def upload_to_db(rows):
    tcount = 0
    scount = 0
    txns = {}
    ss = {}
    for row in rows:
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
        cols = row.split(',');
        if len(cols) == 13 and cols[0] != 'Name' and cols[12] != '""':
            #transactions to upload
            key = cols[10]
            if key not in txns.keys():
                txns[key] = 0
            txns[key] += 1
            #put to db.
            mycursor = mydb.cursor()
            sql = "INSERT IGNORE INTO `transactions` (`Name`,`Applied to Bill`, `Tip`, `Payment Amount`, `Gratuity`, `Bill Date`, `Bill Date Time`, `Bill Number`,`Staff`) VALUES ( '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
            val = (cols[0], cols[1][1:], cols[2][1:], cols[3][1:], cols[8][1:], cols[9].split(' ')[0], cols[9], cols[10] + '_' + str(txns[key]), cols[12])
            mycursor.execute(sql % val)
            mydb.commit()
            tcount += 1
        if len(cols) == 7 and cols[0] != "Name" and cols[1] != '""':
            key = cols[0] + cols[2];
            if key not in ss.keys():
                ss[key] = 0;
            else:
                continue
            #put to db.
            mycursor = mydb.cursor()
            sql = "INSERT IGNORE INTO `shifts` (`dow`, `Name`, `Staff Type`, `Clock-In-Date`, `Clock-In`, `Clock-Out`, `Duration`, `Hourly Rate`, `Pay`) VALUES ( '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'  );";
            dow = datetime.strptime(cols[2], '%Y-%m-%d %H:%M').strftime("%A")[0:3]
            val = (dow, cols[0], cols[1], cols[2].split(' ')[0], cols[2], cols[3], cols[4], cols[5][1:], cols[6][1:] )
            mycursor.execute(sql % val)
            mydb.commit()
            scount += 1
    print "Inserted %d transactions and %d shifts"%(tcount, scount)
try:
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
    typ, accountDetails = imapSession.login(userName, passwd)
    if typ != 'OK':
        print 'Not able to sign in!'
        raise
    
    imapSession.select('[Gmail]/All Mail')
    typ, data = imapSession.search(None, '(UNSEEN)')
    if typ != 'OK':
        print 'Error searching Inbox.'
        raise
    to_delete = []
    # Iterating over all emails
    for msgId in data[0].split():
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print 'Error fetching mail.'
            raise

        emailBody = messageParts[0][1]
        mail = email.message_from_string(emailBody)
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                # print part.as_string()
                continue
            if part.get('Content-Disposition') is None:
                continue
            fileName = part.get_filename()
            if "TemplateReport" not in fileName:
                print "Skip processing " + fileName
                continue
            print "Processing " + fileName
            contents = part.get_payload(decode=True)
            contents = contents.replace('\r', '')
            rows = contents.split('\n')
            upload_to_db(rows)
            #mark the messges to be deleted.
            to_delete.append(msgId)

    for msgId in to_delete:
        print "Deleting message " + str(msgId)
        print imapSession.store(msgId, '+FLAGS', '\\Deleted')
    imapSession.expunge()            
    imapSession.close()
    imapSession.logout()
except Exception as e:
    print 'Not able to download all attachments.' + e.message

mydb.close()
print str(datetime.now())
print "<<<<<< Done"            
        
