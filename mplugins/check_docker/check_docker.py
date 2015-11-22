#!/usr/bin/env python

import sys

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

docker_py_error = False
try:
    from docker import Client
except:
    docker_py_error = True


class CheckDocker(MPlugin):

    def get_stats(self):

        if docker_py_error:
            self.exit(CRITICAL, message="please install docker-py")

        base_url = self.config.get('base_url')

        cli = Client(base_url=base_url)

        try:
            cli.info()
        except:
            self.exit(CRITICAL, message="can not connect to docker client")

        data = []
        ids = []
        name_id = {}
        containers = cli.containers()
        for container in containers:
            ids.append(container['Id'])
            name_id[container['Id']] = container['Names']
        for id in ids:
            stats_obj = cli.stats(id, True)
            for stat in stats_obj:
                stat['id'] = id
                stat['names'] = name_id[id]
                data.append(stat)
                break
        return data


    def run(self):
        stats = self.get_stats()
        data = {}

        for stat in stats:
            data['id'] = stat['id']
            data['names'] = stat['names']
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
                cpu_percent = (cpuDelta / systemDelta) * float(len(stat['precpu_stats']['cpu_usage']['percpu_usage'])) * 100.0
            data['cpu_percent'] = cpu_percent

            data['network'] = stat['network']

            for io in stat['blkio_stats']['io_service_bytes_recursive']:
                if io['op'] == 'Read':
                    data['read'] = io['value']
                if io['op'] == 'Write':
                    data['write'] = io['value']
                if io['op'] == 'Sync':
                    data['sync'] = io['value']
                if io['op'] == 'Async':
                    data['async'] = io['value']

        metrics = {
            'CPU and Memory usage': {
                'CPU percentage': data['cpu_percent'],
                'Memory percentage': data['mem_percent']
            },
            'Network Usage': {
                'Transmitted Bytes': data['tx_bytes'],
                'Recieved Bytes': data['rx_bytes']
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
