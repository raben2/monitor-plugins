#!/usr/bin/env python

import sys

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

from docker import Client


class CheckDocker(MPlugin):

    def get_stats(self):
        # address can be socket: 'unix://var/run/docker.sock' or tcp: 'tcp://127.0.0.1:2375'
        address = self.config.get('address')
        cli = Client(base_url=address)
        try:
            return cli.containers(quiet=False, all=True, trunc=False, latest=False, since=None, before=None, limit=-1, size=False, filters=None)
        except:
            self.exit(CRITICAL, message="invalid base url")


    def run(self):
        data = self.get_stats()
        
        counter_data = [

        ]
        
        gauge_data = [

        ]
        
        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx, 0))
            except ValueError:
                tmp_counter[idx] = data.get(idx, 0)
        
        tmp_counter = self.counters(tmp_counter, 'memcache')
      
        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx, 0))
            except ValueError:
                tmp_gauge[idx] = data.get(idx, 0)
                        
        data = tmp_counter.copy()
        data.update(tmp_gauge)
        
        get_hits = int(data['get_hits'])
        get_misses = int(data['get_misses'])
        try:
            data['hit_percentage'] = (get_hits/(get_hits+get_misses)) * 100
            data['miss_percentage'] = (get_misses/(get_hits+get_misses)) * 100
        except ZeroDivisionError:
            data['hit_percentage'] = 0
            data['miss_percentage'] = 0
        
        metrics = {
            'usage': {
                'user time': data['rusage_user'],
                'system time': data['rusage_system']
            }
        }
        self.exit(OK, data, metrics)    
                  
if __name__ == '__main__':    
    monitor = CheckDocker()
    monitor.run()
