#!/usr/bin/env python
import string
import sys
import syslog
import time
import MySQLdb
import datetime
from os.path import expanduser

import smtplib
from email.mime.text import MIMEText

first_time = 1

interval = 1800

log = syslog.openlog("check-ap", syslog.LOG_PID)
syslog.syslog(syslog.LOG_INFO, "start check-ap...%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

while True:
    syslog.syslog(syslog.LOG_INFO,"Checking on %s " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    find_subject = ""
    missing_subject = ""
    db = MySQLdb.connect("localhost", "dev", "dev", "dev")
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    sqlstring = "select topic from  `mqtt` order by ts desc limit 40"
    cursor.execute(sqlstring)
    topics = cursor.fetchall()

    sqlstring = "select src_apstation from  `aplist`"
    cursor.execute(sqlstring)

    aplist = cursor.fetchall()
    syslog.syslog(syslog.LOG_INFO, str(aplist))
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

    now = datetime.datetime.now()
    delta_m = now.minute
    delta_s = now.second + delta_m * 60
    if first_time != 1:
        # not the fist time
        first_time = 0
        if (len(missing_subject) == 0):
            #sys.exit()
            syslog.syslog(syslog.LOG_INFO,"All find!")
            # 
            #now = datetime.datetime.now()
            #delta_m = now.minute
            #delta_s = now.second + delta_m * 60
            if delta_s  >= interval:
                syslog.syslog(syslog.LOG_INFO,"Current minute+second too high!  m=%d s=%d sleep %d" % (delta_m, delta_s, interval))
                time.sleep(interval)
                continue
        else:
            syslog.syslog(syslog.LOG_ERR,"AP missing! Send out mail!")
    else:
        # first time, send mail always
        first_time = 0

#  delta_s < interval 
# send mail
    sender = "sdssly2@sina.com"
    receiver = "28277961@qq.com"
    cc = "sdssly2@sina.com,sdssly@sina.com"
    content = "List:\r\n" + missing_subject + find_subject
    
    syslog.syslog(syslog.LOG_INFO,"content:%s" % content)
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
    syslog.syslog(syslog.LOG_INFO,"msg: %s %s " % (msg, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    rcpt = cc.split(",") + [receiver]
    try:
        server.sendmail(sender, rcpt , msg.as_string())
        #print("quit")
        #server.quit()
    except smtplib.SMTPException as e:
        syslog.syslog(syslog.LOG_ERR,"error send [%s] sleep ...%d" % (str(e), interval))
        time.sleep(interval)
        #interval += interval
    else:    
        syslog.syslog(syslog.LOG_INFO,"Send mail okay! quit server")
        server.quit()
    
    # Adjust time
    syslog.syslog(syslog.LOG_INFO,"sleep- m=%d s=%d interval=%d" % (delta_m, delta_s, interval))
    if interval > delta_s:
        time.sleep(interval - delta_s)
    else:
        time.sleep(interval)


