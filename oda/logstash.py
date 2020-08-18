import socket
import json
import sys
import os

import logging

class LogStasher:
    def __init__(self, url = None):
        if url is None:
            url = self.choose_url()            

        self.url = url
        self.context = {}

    def choose_url(self):
        failures=[]

        logstash_entrypoint = None

        for method_name, method in [
            ('env', lambda : os.environ.get("LOGSTASH_ENTRYPOINT",None)),
            ('cdci resources', lambda : open("/cdci-resources/logstash-entrypoint").read().strip()),
        ]:
            try:
                logstash_entrypoint = method()
                if logstash_entrypoint is None or logstash_entrypoint.strip() == "":
                    raise Exception("entrypoint is None or empty")
                break
            except Exception as e:
                failures.append(("unable to get logstash entrypoint from method", method_name,"exception:",e))
                logging.debug(repr(failures[-1]))

        return logstash_entrypoint
                

    def set_context(self, c):
        self.context = c
    
    def log(self, msg):
        if self.url is None:
            logging.debug("fallback logstash: %s", msg)
            return
        
        HOST, PORT = self.url.split(":")
        PORT = int(PORT)

        msg = dict(list(self.context.items()) + list(msg.items()))

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            logging.error("[ERROR] %s\n" % repr(e)) 
            

        try:
            sock.connect((HOST, PORT))
        except Exception as e:
            logging.error("[ERROR] %s\n" % repr(e)) 

        sock.send(json.dumps(msg).encode())

        sock.close()
