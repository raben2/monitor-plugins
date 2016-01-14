#!/usr/bin/env python

import urllib2
import json

from sys import exit
from optparse import OptionParser, OptionGroup

import sys
sys.path.append('/opt/ecmanaged/ecagent/plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


class ElasticSearchStatus(MPlugin):
    def call_to_cluster(self, host, path):
        """Call a given path to the cluster and return JSON."""

        try:
            r = urllib2.urlopen('{h}{p}'.format(h=host, p=path))
        except (urllib2.URLError, ValueError) as e:
            self.exit(CRITICAL, message=e)

        try:
            response = json.loads(r.read())
        except Exception as e:
            self.exit(CRITICAL, message=e)

        return response

    def get_stats(self, host, keyname):
        """Return a dict of stats from /_cluster/nodes/_local/stats.
        Keyname can be one of: docs, search, indexing, store, get"""

        h = self.call_to_cluster(host, '/_cluster/nodes/_local/stats')

        node_name = h['nodes'].keys()[0]
        stats = h['nodes'][node_name]['indices'][keyname]

        return stats

    def cluster_health(self, host):
        """Print metrics about /_cluster/health."""

        h = self.call_to_cluster(host, '/_cluster/health')

        data = {'number_of_nodes': h['number_of_nodes'], 'unassigned_shards': h['unassigned_shards'],
                'timed_out': h['timed_out'], 'active_primary_shards': h['active_primary_shards'],
                'relocating_shards': h['relocating_shards'], 'active_shards': h['active_shards'],
                'initializing_shards': h['initializing_shards'], 'number_of_data_nodes': h['number_of_data_nodes']}

        return data

    def stats_store(self, host):
        """Print store metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'store')

        data = {'size_in_bytes': s['size_in_bytes'], 'throttle_time_in_millis': s['throttle_time_in_millis']}

        return data

    def stats_indexing(self, host):
        """Print indexing metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'indexing')

        data = {'delete_time_in_millis': s['delete_time_in_millis'], 'delete_total': s['delete_total'],
                'delete_current': s['delete_current'], 'index_time_in_millis': s['index_time_in_millis'],
                'index_total': s['index_total'], 'index_current': s['index_current']}

        return data

    def stats_get(self, host):
        """Print GET metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'get')

        data = {'missing_total': s['missing_total'], 'exists_total': s['exists_total'], 'current': s['current'],
                'total': s['total']}

        return data

    def stats_search(self, host):
        """Print search metrics from /_cluster/nodes/_local/stats."""

        s = self.get_stats(host, 'search')

        data = {'query_total': s['query_total'], 'fetch_time_in_millis': s['query_time_in_millis'],
                'fetch_total': s['fetch_total'], 'query_time_in_millis': s['fetch_time_in_millis'],
                'open_contexts': s['open_contexts'], 'fetch_current': s['fetch_current'],
                'query_current': s['query_current']}

        return data

    def stats_docs(self, host):
        '''Print doc metrics from /_cluster/nodes/_local/stats.'''

        s = self.get_stats(host, 'docs')

        print "metric count uint64", s['count']
        print "metric deleted uint32", s['deleted']

    def run(self):
        host = self.config.get('hostname','localhost')


if __name__ == '__main__':
    monitor = ElasticSearchStatus()
    monitor.run()