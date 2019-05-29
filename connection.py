#!/usr/bin/python3

#run with python -u connection.py 192.168.1.2 9226 | mosquitto_pub -t Energy -l

from xml.dom.minidom import parse
import xml.dom.minidom
import re
import time
import telnetlib
import csv
import sys

PRECMD = "stream:42:val?com=gmp&mid="
POSTCMD= ".1&regt=010a00\n"

def connect_telnet(host):
    tn=telnetlib.Telnet(host,"7777")
    tn.read_until('stream:7:granted')
#    print 'Connected to IK30'
    return tn

def send_neuros_id(tn, nid):
    tn.write(PRECMD + nid + POSTCMD)

def parse_ik30_resp(tn):
    ( i, obj, res) = tn.expect(['</resp>','</values>'],5)
#    print "switch %d" % i
    if i==0:
        regex = re.compile('stream:\d+:')
        ex = regex.findall(res)
        #    print ex
        resp = res.replace(ex[0],'')
#        print resp

        regex = re.compile('>([^<]+)<')
        ex = regex.findall(res)
        #    print ex
        res = ex[0].replace("<",'')
        #    print res
        ret_val = res.replace(">",'')
        return int(ret_val) 
    if i==1:
#        print res
#        print "next1"
        regex = re.compile('stream:\d+:')
        ex = regex.findall(res)
#        print ex
        res = res.replace(ex[0],'')
#        print res
        DOMTree = xml.dom.minidom.parseString(res)
        response = DOMTree.documentElement
#        if response.hasAttribute("itag"):
#           print ("Root itag : %s" % response.getAttribute("itag"))

        cid = response.getElementsByTagName("cid")[0]
#        print ("Cid: %s" % cid.firstChild.data)
        sdata = response.getElementsByTagName("sdata")[0]
        valg = sdata.getElementsByTagName("valg")[0]
        val = valg.getElementsByTagName("val")[0]
#        print ("val: %s" % val.firstChild.data)
        return int(val.firstChild.data)

def get_kWh_answer(tn):
    # parse first response
    ret = parse_ik30_resp(tn)
#    if ret==0:
#        print "Query ok %d\n" % ret

    if ret==0:
        # parse second response
        ret = parse_ik30_resp(tn)
        if ret == -2:
#            print "Query error %d\n" % ret
            return ret
        if ret > 0:
#            print "Current kWh %d\n" % ret
            return ret


tn = connect_telnet(sys.argv[1])

with open(sys.argv[2]+'.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        send_neuros_id(tn, row['neurosid'])
        kWh = get_kWh_answer(tn)
        print "{ \"id\": %s, \"net\": %s, \"kWh\": %d }" % (row['id'], sys.argv[2], kWh)




