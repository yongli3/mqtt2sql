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

# there are some not found items!
missing = 1
default_interval = 3600
interval = default_interval

log = syslog.openlog("check-ap", syslog.LOG_PID)
syslog.syslog(syslog.LOG_INFO, "start check-ap...%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

while True:
    syslog.syslog(syslog.LOG_INFO,"Checking on %s " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    find_subject = ""
    missing_subject = ""
    lora_ok = ""
    lora_fail = ""

    db = MySQLdb.connect("localhost", "dev", "dev", "dev")
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    
    sqlstring = "select topic from  `mqtt` where ts > (now() - interval 20 minute) order by ts desc"
    #sqlstring = "select topic from  `mqtt` order by ts desc limit 45"
    cursor.execute(sqlstring)
    topics = cursor.fetchall()

    sqlstring = "select src_apstation from  `rawdata` where `timestamp` > (now() - interval 480 minute) order by `timestamp` desc"
    cursor.execute(sqlstring)
    rawdatas = cursor.fetchall()

    sqlstring = "select src_apstation from  `aplist` where monitor = 1 order by src_apstation"
    cursor.execute(sqlstring)
    aplist = cursor.fetchall()
    syslog.syslog(syslog.LOG_INFO, str(aplist))
    for row in aplist:
        ap = row["src_apstation"]
        #print("AP = %s" % ap)
        find = 0
        for topic in topics:
            #print("topic = %s" % topic["topic"])
            ap_topic = topic["topic"].split('-')[0]
            #print("ap_topic=%s" % ap_topic)
            if (ap_topic == str(ap)):
                #print("Find! " + str(ap)) 
                find = 1
                break

        lora = 0
        for rawdata in rawdatas:
            #print("rawdata = %s" % rawdata["src_apstation"])
            if (rawdata["src_apstation"] == ap):
                #print("Lora! " + str(ap))
                lora = 1
                break

        if find == 1:
            #subject = subject.format("{0} find!\r\n", ap)
            find_subject = "%s AP %d online!\r\n" % (find_subject, ap)
        else:
            missing_subject = "%s AP %d offline!\r\n" % (missing_subject, ap)

        if lora == 1:
            lora_ok = "%s AP %d LORA data okay!\r\n" % (lora_ok, ap)
        else:
            lora_fail = "%s AP %d LORA data Fail!\r\n" % (lora_fail, ap)

    db.commit()
    db.close()

    #print("query DB finish.")
    #print(find_subject)
    #print(missing_subject)
    #print(lora_ok)
    #print(lora_fail)	
    #quit()

    now = datetime.datetime.now()
    s1 = now.second + now.minute * 60
    delta_m = now.minute
    delta_s = now.second + delta_m * 60
    if first_time != 1:
        # not the fist time
        first_time = 0
        if (len(missing_subject) == 0):
            #sys.exit()
            if missing == 1:
                # restore from missing status, must out mail
                missing = 0
            
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
            missing = 1
            syslog.syslog(syslog.LOG_ERR,"AP missing! Send out mail!")
    else:
        # first time, send mail always
        first_time = 0

    #print("query DB okay...")
    #quit()
#  delta_s < interval 
# send mail
    sender = "sdssly2@sina.com"
    receiver = "28277961@qq.com"
    cc = "sdssly2@sina.com"
    
    #
    if (len(missing_subject) == 0):
        find_subject = "ALL online!"

    content = "List:\r\n" + missing_subject + find_subject
    content += "\r\n\r\nLORA:\r\n" + lora_fail
    print("content=%s" % content)
    syslog.syslog(syslog.LOG_INFO,"content:%s" % str(content))
    msg = MIMEText(content)
    msg['From'] = sender
    msg['To'] = receiver
    msg['Cc'] = cc
    msg['Subject'] = "Running AP Report %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #quit()

    server = smtplib.SMTP_SSL('{}:{}'.format("smtp.sina.com", "465"))
    server.login("sdssly2", "MqttAdmin98")
    #server.send_message(msg)
    message = "From %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % (sender, receiver, msg['Subject'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content)
    #print("message: %s %s " % (message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    syslog.syslog(syslog.LOG_INFO,"msg: %s %s " % (msg, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    rcpt = cc.split(",") + [receiver]
    
    #now = datetime.datetime.now()
    #s1 = now.second + now.minute * 60
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
    
    now = datetime.datetime.now()
    s2 = now.second + now.minute * 60
    # Adjust time
    syslog.syslog(syslog.LOG_INFO,"sleep- s1=%d s2=%d interval=%d" % (s1, s2, interval))
    #if interval > delta_s:
    #    time.sleep(interval - delta_s)
    #else:
    time.sleep(interval - (s2 - s1))


