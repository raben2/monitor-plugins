#!/usr/bin/env python

import sys
sys.path.append('/opt/ecmanaged/ecagent/plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT


class MySQLStatus(MPlugin):
    def get_stats(self):
        host = self.config.get('host')
        user =self.config.get('user')
        password = self.config.get('password')

        try:
            import MySQLdb as Database
        except ImportError:
            self.exit(CRITICAL, message="Please install MySQL-python")
        
        try:
            self.conn = Database.connect(host=host, user=user, passwd=password)
        except:
            self.exit(CRITICAL, message="Unable to connect to MySQL Database")
        
        try:
            conn_cursor = self.conn.cursor(Database.cursors.DictCursor)
            conn_cursor.execute('SHOW GLOBAL STATUS;')
            result = conn_cursor.fetchall()
        except:
            self.exit(CRITICAL, message="Unable to run SHOW GLOBAL STATUS")
        
        return dict(map(lambda x: (x.get('Variable_name'), x.get('Value')),result))
    
    def run(self):
        data = self.get_stats()
        
        counter_data = [
            'Connections',
            'Aborted_clients',
            'Aborted_connects',
            'Bytes_received',
            'Bytes_sent',
            'Innodb_data_read',
            'Innodb_data_written',
            'Innodb_rows_deleted',
            'Innodb_rows_inserted',
            'Innodb_rows_read',
            'Innodb_rows_updated',
            'Queries',
            'Questions',
            'Slow_queries'               
        ]
        
        gauge_data = [
            'Innodb_buffer_pool_pages_data',
            'Innodb_buffer_pool_pages_dirty',
            'Innodb_buffer_pool_pages_free',
            'Innodb_pages_created',
            'Innodb_pages_read',
            'Innodb_pages_written',
            'Innodb_row_lock_current_waits',
            'Innodb_row_lock_time',
            'Innodb_row_lock_time_avg',
            'Innodb_row_lock_time_max',
            'Innodb_row_lock_waits',
            'Open_files',
            'Open_streams',
            'Open_table_definitions',
            'Open_tables',
            'Slow_launch_threads',
            'Threads_cached',
            'Threads_connected',
            'Threads_created',
            'Threads_running',
            'Handler_delete',
            'Handler_read_first',
            'Handler_read_rnd',
            'Handler_read_rnd_next',
            'Handler_update',
            'Handler_write',
            'Created_tmp_disk_tables',
            'Created_tmp_files',
            'Created_tmp_tables',
            'Qcache_free_memory',
            'Qcache_hits',
            'Qcache_queries_in_cache'
        ]
        
        tmp_counter = {}
        for idx in counter_data:
            try:
                tmp_counter[idx] = int(data.get(idx,0))
            except:
                tmp_counter[idx] = data.get(idx,0)
        
        tmp_counter = self.counters(tmp_counter,'mysql')
      
        tmp_gauge = {}
        for idx in gauge_data:
            try:
                tmp_gauge[idx] = int(data.get(idx,0))
            except:
                tmp_gauge[idx] = data.get(idx,0)
                        
        data = tmp_counter.copy()
        data.update(tmp_gauge)
    
        metrics = {
            'Traffic': { 
              'Bytes recieved': data['Bytes_received'],
              'Bytes sent': data['Bytes_sent']
            },
            'Temp': {
              'Tmp disk tables': data['Created_tmp_disk_tables'],
              'Tmp file': data['Created_tmp_files'],
              'Tmp tables': data['Created_tmp_tables'] 
            },
            'Handlers': {
              'Delete': data['Handler_delete'],
              'Read first': data['Handler_read_first'],
              'Read random': data['Handler_read_rnd'],
              'Read random next': data['Handler_read_rnd_next'],
              'Update': data['Handler_update'],
              'Write': data['Handler_write']
            },
            'Qcache': {
              'Free memory': data['Qcache_free_memory'],
              'hits': data['Qcache_hits'],
              'Queries in cache': data['Qcache_queries_in_cache']
            },
            'Threads': {
              'Connected': data['Threads_connected'],
              'Created': data['Threads_created'],
              'Running': data['Threads_running'],
              'Slow launch': data['Slow_launch_threads'],
              'Cached': data['Threads_cached']
            },
            'Connections': {
              'Connection attempts': data['Connections'],
              'Aborted clients': data['Aborted_clients'],
              'Aborted connections': data['Aborted_connects']
            },
            'InnoDB data stats': {
              'Data read': data['Innodb_data_read'],
              'Data written': data['Innodb_data_written']
            },
            'InnoDB row stats':  {
              'Rows deleted': data['Innodb_rows_deleted'],
              'Rows inserted': data['Innodb_rows_inserted'],
              'Rows read': data['Innodb_rows_read'],
              'Rows updated': data['Innodb_rows_updated']
            },
            'Queries':  {
              'Statements executed': data['Queries'],
              'Statements executed by clients': data['Questions'],
              'Slow queries': data['Slow_queries']
            },
            'Innodb buffer pool pages stats': {
              'Pages containing data': data['Innodb_buffer_pool_pages_data'],
              'Dirty pages': data['Innodb_buffer_pool_pages_dirty'],
              'Free pages': data['Innodb_buffer_pool_pages_free']
            },
            'Innodb pages stats':  {
              'Created': data['Innodb_pages_created'],
              'Read': data['Innodb_pages_read'],
              'Written': data['Innodb_pages_written']
            },
            'Innodb row lock stats':  {
              'Currently being waited': data['Innodb_row_lock_current_waits'],
              'Time spent in acquiring ': data['Innodb_row_lock_time'],
              'Average time to acquire': data['Innodb_row_lock_time_avg'],
              'Maximum time to acquire': data['Innodb_row_lock_time_max'],
              'Number of times waited': data['Innodb_row_lock_waits']
            }
            
        }
        
        self.exit(OK, data, metrics) 

if __name__ == '__main__':    
    monitor = MySQLStatus()
    monitor.run()