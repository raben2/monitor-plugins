#!/usr/bin/env python

import sys
sys.path.append('/opt/ecmanaged/ecagent/plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


# pip install python-memcached
import_error = False
try:
    from pymongo import MongoClient
except:
    import_error = True


class MongoDBStatus(MPlugin):

    def get_stats(self, hostname, port, database):
        client = MongoClient(host=hostname, port=port)
        db = client[database]
        data = None
        try:
            data = db.command("dbstats")
        except:
            self.exit(CRITICAL, message="can not connect to mongodb")
        return data

    def run(self):
        if import_error:
            self.exit(CRITICAL, message="Please install pymongo")

        hostname = self.config.get('hostname','localhost')
        port = self.config.get('port','27017')
        database = self.config.get('database')

        data = self.get_stats(hostname, port, database)

        if not data:
            self.exit(CRITICAL, message="can not obtain stat")
        
        metrics = {}

        self.exit(OK, data, metrics)    
                  
if __name__ == '__main__':    
    monitor = MongoDBStatus()
    monitor.run()