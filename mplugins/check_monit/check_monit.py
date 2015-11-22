#!/usr/bin/env python

# based on monit.py by Camilo Polymeris, 2015
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import requests
import simplejson as json

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL

root_dir = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = (root_dir + '/persistent.data')
MIN_METRICS = 3


class Monit(MPlugin):
    def run(self):
        username = self.config.get('user','')
        password = self.config.get('pass','')
        port     = self.config.get('port')
        
        try:
            mons = MonitConn(username=username, password=password, port=port)

        except:
            self.exit(CRITICAL, message="Unable to connecto to monit API")
  
        data = {}
        metrics = {}
        msglist = []
        result = OK

        for mon in mons.keys():
            state = mons[mon].running
            enabled = mons[mon].monitored
            type = mons[mon].type
            name = mons[mon].name
            extra = mons[mon].data
            
            if not name:
                continue
            
            if not state:
                result = CRITICAL
                msglist.append(name.upper() + ' is not running')
                
            if not enabled:
                result = CRITICAL
                msglist.append(name.upper() + ' is not monitored')
                
            # Custom name
            name = name + ': ' + type
            
            # Add data
            data[name] = {
                'type': type,
                'state': state,
                'enabled': enabled,
                'data': extra
            }
            
            # Create metrics
            metrics[name] = {}
            count_metrics = 0
            
            for k in extra.keys():
                metrics[name][k] = extra[k]
                count_metrics = count_metrics + 1
            
            # Add placeholder for metrics (each monit has to have the same number of metrics)    
            for i in range(count_metrics, MIN_METRICS):
                metrics[name]['__ph__' + str(i)] = ''

        if not msglist:
            msglist.append('ALL ' + str(len(data.keys())) + ' MONIT SERVICES ARE OK')
            
        self.exit(result, data, metrics, message=' / '.join(msglist))
        
class MonitConn(dict):
    def __init__(self, host='localhost', port=2812, username=None, password='', https=False):
    
        if not port:
            port = 2812
            
        port = int(port)
        self.baseurl = (https and 'https://%s:%i' or 'http://%s:%i') % (host, port)
        self.auth = None
        
        if username:
            self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.update()
    
    def update(self):
        """
        Update Monit deamon and services status.
        """
        url = self.baseurl + '/_status?format=xml'
        response = requests.get(url, auth=self.auth)
        
        from xml.etree.ElementTree import XML
        root = XML(response.text)
        
        for serv_el in root.iter('service'):
            serv = MonitConn.Service(self, serv_el)
            self[serv.name] = serv
            
    class Service:
        """
        Describes a Monit service, i.e. a monitored resource.
        """
        def __init__(self, daemon, xml):
            """
            Parse service from XML element.
            """
	    self.xml = xml
            self.data = {}
            self.perfdata = ''
            self.name = self._xmlfind('name')
            self.type = {
                0: 'filesystem',
                1: 'directory',
                2: 'file',
                3: 'process',
                4: 'connection',
                5: 'system'
            }.get(int(xml.attrib['type']), 'unknown')
            self.daemon = daemon
            self.running = True

            if self.type != 'system':
                self.running = not bool(int(self._xmlfind('status')))
                
            if self.type == 'filesystem':
		self.data['percent'] = self._xmlfind('block/percent')
                
            elif self.type == 'system':
                cpu_user = self._xmlfind('system/cpu/user','float')
                cpu_system = self._xmlfind('system/cpu/system','float')
                cpu_wait = self._xmlfind('system/cpu/wait','float')
                
                self.data['cpu']    = int(cpu_user + cpu_system + cpu_wait)
		self.data['memory'] = self._xmlfind('system/memory/percent')
		self.data['swap']   = self._xmlfind('system/swap/percent')

            elif self.type == 'process':
		self.data['memory']    = self._xmlfind('memory/percent')
		self.data['cpu']       = self._xmlfind('cpu/percent')
		self.data['childrens'] = self._xmlfind('children')
            
            elif self.type == 'file':
                self.data['size'] = self._xmlfind('size')
                
            self.monitored = bool(int(self._xmlfind('monitor')))
        
        def _action(self, action):
            url = self.daemon.baseurl + '/' + self.name
            requests.post(url, auth=self.daemon.auth, data={'action': action})
            self.daemon.update()

	def _xmlfind(self, key, type='text'):
	    retval = ''
	    try: 
	        retval = self.xml.find(key).text
	        if type == 'float':
	            retval = float(retval)
	            
	        if type == 'int':
	            retval = int(retval)
	        
            except: pass
            
            if not retval and type != 'text':
                retval = 0
            
            return retval
        
        def __repr__(self):
            repr = self.type.capitalize()
            if not self.running is None:
                repr += self.running and ', running' or ', stopped'
                
            if not self.monitored is None:
                repr += self.monitored and ', monitored' or ', not monitored'
                
            return repr


monitor = Monit()
monitor.run()
