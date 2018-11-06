#!/usr/bin/env python
import string
import sys
import time
import MySQLdb
import datetime
from os.path import expanduser

import smtplib
from email.mime.text import MIMEText

interval = 1200

while True:
    print("Checking on %s " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    find_subject = ""
    missing_subject = ""
    db = MySQLdb.connect("localhost", "dev", "dev", "dev")
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    sqlstring = "select topic from  `mqtt` order by ts desc limit 10"
    cursor.execute(sqlstring)
    topics = cursor.fetchall()

    sqlstring = "select src_apstation from  `aplist`"
    cursor.execute(sqlstring)

    aplist = cursor.fetchall()
    print(aplist)
    for row in aplist:
        ap = row["src_apstation"]
        #print(ap)
        find = 0
        for topic in topics:
            #print(topic.topic)
            ap_topic = topic["topic"].split('-')[0]
            #print(ap_topic)
            if (ap_topic == str(ap)):
                #print("Find! " + str(ap)) 
                find = 1
                break
        if find == 1:
            #subject = subject.format("{0} find!\r\n", ap)
            find_subject = "%s AP %d found!\r\n" % (find_subject, ap)
        else:
            missing_subject = "%s AP %d NOT found!\r\n" % (missing_subject, ap)

    db.commit()
    db.close()


    if (len(missing_subject) == 0):
        #sys.exit()
        print("All find!")
        # 
        now = datetime.datetime.now()
        delta_m = now.minute
        delta_s = now.second + delta_m * 60
        if delta_s  >= interval:
            print("m=%d s=%d sleep %d" % (delta_m, delta_s, interval))
            time.sleep(interval)
            continue
    else:
        print("AP missing! Send out mail!")

# send mail
    sender = "sdssly2@sina.com"
    receiver = "28277961@qq.com"
    cc = "sdssly2@sina.com,sdssly@sina.com"
    content = "List:\r\n" + missing_subject + find_subject
    
    print("content:%s" % content)
    '''
    msg = MIMEText(content)
    msg['From'] = sender
    msg['To'] = receiver
    msg['Cc'] = cc
    msg['Subject'] = "Running AP Report %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    server = smtplib.SMTP_SSL('{}:{}'.format("smtp.sina.com", "465"))
    server.login("sdssly2", "MqttAdmin98")
    #server.send_message(msg)
    message = "From %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % (sender, receiver, msg['Subject'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content)
    #print("message: %s %s " % (message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("msg: %s %s " % (msg, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    rcpt = cc.split(",") + [receiver]
    server.sendmail(sender, rcpt , msg.as_string())
    server.quit()
    '''
    # Adjust time
    print("sleep- m=%d s=%d" % (delta_m, delta_s))
    time.sleep(interval - delta_s)

