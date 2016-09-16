#!/usr/bin/env python
# This file is part of the api monitoring plugins
# Maintainer Georg Rabenstein @raben2
# git@github.com:raben2/monitor-plugins.git

import sys
from optparse import OptionParser
from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

docker_py_error = False
try:
    from docker import Client
except:
    docker_py_error = True


class CheckDocker(MPlugin):
    def get_stats(self, base_url, container_name):
        cli = Client(base_url=base_url)

        try:
            cli.info()
        except:
            self.exit(CRITICAL, message="can not connect to docker client")

        containers = cli.containers()
        id = None
        ignore_networks = "host"

        for container in containers:
            if container['Names'][0].split('/')[-1] == container_name:
                id = container['Id']
                nm = container['HostConfig']['NetworkMode']
                break
        if id:
            stats_obj = cli.stats(id, True)

            for data in stats_obj:
                return data, nm
                    
        return None

    def run(self):
        if docker_py_error:
            self.exit(CRITICAL, message="please install docker-py")
        usage = "usage: %prog -H hostname -C Container"
        parser = OptionParser(usage=usage)
        parser.add_option("-H", "--host", dest="base_url", help="Docker Host", metavar="HOST")
        parser.add_option("-C", "--container", dest="container_name", help="docker container", metavar="CONTAINER")
        parser.add_option("-M", "--metric", dest="metric", help="Metric to be checked: CPU, NET or HDD", metavar="METRIC", default="ALL")

        if len(sys.argv) < 2:
           parser.print_help()
           sys.exit(-1)
        else:
           (options, args) = parser.parse_args()
           base_url = 'tcp://' + options.base_url.lower() + ':2375'
           container_name = options.container_name
           metric = options.metric
        try:
          stat, nm = self.get_stats(base_url, container_name)
        except TypeError:
            self.exit(CRITICAL, message="Container %s is not runnung" %container_name)
        if not stat:
            self.exit(CRITICAL, message="No container found with name: %s" %container_name)
        data = {}
        counter_data = [
            'read',
            'write',
            'sync',
            'async',
            'network_tx_bytes',
            'network_rx_bytes'
        ]

        gauge_data = [
            'cpu_percent',
            'mem_percent'
        ]

        mem_percent = 0
        cpu_percent = 0

        if stat['memory_stats']['limit'] != 0:
            mem_percent = float(stat['memory_stats']['usage']) / float(stat['memory_stats']['limit']) * 100.0
        data['mem_percent'] = mem_percent

        previousCPU = stat['precpu_stats']['cpu_usage']['total_usage']
        previousSystem = stat['precpu_stats']['system_cpu_usage']

        cpuDelta = stat['cpu_stats']['cpu_usage']['total_usage'] - previousCPU
        systemDelta = stat['cpu_stats']['system_cpu_usage'] - previousSystem

        if systemDelta > 0 and cpuDelta > 0:
            cpu_percent = (float(cpuDelta) / float(systemDelta)) * float(len(stat['cpu_stats']['cpu_usage']['percpu_usage'])) * 100.0
        data['cpu_percent'] = cpu_percent

        if nm != "host":
          try:
            data['network'] = stat['networks']['eth0']
            data['network_tx_bytes']= data['network']['tx_bytes']
            data['network_rx_bytes'] =data['network']['rx_bytes']
          except KeyError:
            data['network'] = stat['pid_stats']
            data['network_tx_bytes']= data['network']['tx_bytes']
            data['network_rx_bytes'] =data['network']['rx_bytes']       

        data['read'] = 0
        data['write'] = 0
        data['sync'] = 0
        data['async'] = 0

        for io in stat['blkio_stats']['io_service_bytes_recursive']:
            if io['op'] == 'Read':
                data['read'] = io['value']
            if io['op'] == 'Write':
                data['write'] = io['value']
            if io['op'] == 'Sync':
                data['sync'] = io['value']
            if io['op'] == 'Async':
                data['async'] = io['value']

        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)

        tmp_counter = self.counters(tmp_counter,'docker')

        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)

        data = tmp_counter.copy()
        data.update(tmp_gauge)

        if metric == "CPU":  

              metrics = {
                'CPU and Memory usage': {
                    'CPU percentage': data['cpu_percent'],
                    'Memory percentage': data['mem_percent']
                  }
             }
        elif metric == "NET":

             metrics = {
                'Network Usage': {
                    'Transmitted Bytes': data['network_tx_bytes'],
                    'Recieved Bytes': data['network_rx_bytes']
                  }
             }
        elif metric == "HDD":

             metrics = {
                'Block I/O': {
                    'Read': data['read'],
                    'Write': data['write'],
                    'Sync': data['sync'],
                    'Async': data['async']
                }    

            }
        elif metric == "ALL":
             metrics = {
                'CPU and Memory usage': {
                    'CPU percentage': data['cpu_percent'],
                    'Memory percentage': data['mem_percent']
                  },
                'Network Usage': {
                    'Transmitted Bytes': data['network_tx_bytes'],
                    'Recieved Bytes': data['network_rx_bytes']
                  },
                'Block I/O': {
                    'Read': data['read'],
                    'Write': data['write'],
                    'Sync': data['sync'],
                    'Async': data['async']
                }    

            }       
        self.exit(OK, data, metrics)
                  
if __name__ == '__main__':    
    monitor = CheckDocker()
    monitor.run()
