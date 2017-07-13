#!/usr/bin/python3

import boto.ec2.cloudwatch
import socket
import struct
import configparser
import sys
import datetime
import syslog

class ZabbixAgent:
    def __init__(self, host, port, timeout, request):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self.request = request.encode('UTF-8')
        self.value = 0.0

    def _unpack_answer(self, data):
        header = struct.Struct("<4sBQ")
        (prefix, version, length) = header.unpack(data[:13])
        payload = struct.Struct("<%ds" % length)
        self.value = float(payload.unpack(data[13:])[0])

    def query_zabbix_agent(self):
        zsocket = None
        try:
            zsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            zsocket.settimeout(self.timeout)
            zsocket.connect((self.host, self.port))
            zsocket.send(self.request)
            data = b''
            chunk = " "
            while chunk:
                chunk = zsocket.recv(1024)
                data = data + chunk
            if len(data) > 13:
                self._unpack_answer(data)
        except socket.timeout as err:
            syslog.syslog('Zabbix host: %s Error: %s' % (self.host, str(err)))
        except socket.gaierror as err:
            syslog.syslog('Zabbix host: %s Error: %s' % (self.host, str(err)))
        except ConnectionRefusedError as err:
            syslog.syslog('Zabbix Port: %s Error: %s' % (self.port, str(err)))
        except BlockingIOError as err:
            syslog.syslog('Please check timeout parameter in config file. Error: %s' % str(err))
        finally:
            zsocket.close()

if __name__ == '__main__':
    try:
        metric = sys.argv[1]
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_LOCAL7)
        monconf = configparser.ConfigParser()
        monconf.read('/etc/sitm.conf')
        cwatch = boto.ec2.cloudwatch.connect_to_region(monconf.get('common','region'))
        zagent = ZabbixAgent(monconf.get('common', 'host'),
                          monconf.get('common', 'port'),
                          monconf.get('common', 'socket_timeout'),
                          monconf.get(metric, 'key'))
        zagent.query_zabbix_agent()
        cwatch.put_metric_data(monconf.get(metric, 'namespace'),
                      [metric],
                      [zagent.value],
                      datetime.datetime.now(),
                      monconf.get(metric, 'unit'),
                      {'InstanceId': [monconf.get('common', 'instance-id')]})
    except IndexError as err:
        syslog.syslog(str(err))
    except boto.exception.BotoServerError as err:
        syslog.syslog(str(err))
