#!/usr/bin/env python
import sys
import shlex
import subprocess

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL, TIMEOUT

class RunCmd(MPlugin):
    def run(self):
        cmd = self.config.get('cmd')

        # Verify URL
        if not url:
            self.exit(CRITICAL, message="no commands found")


        data = self._run_command(cmd)
        metrics = {
            'Connections': {
                'accepted conn': self._counter(data['accepted conn'],'accepted conn')
            },
            'Processes': {
               'idle processes': data['idle processes'],
               'active processes': data['active processes'],
               'total processes': data['total processes']
            }
        }
        
        self.exit(OK,data,metrics)
        
    def _run_command(self, cmd):
        commands = cmd.split('|')
        res = ''
        for command in commands:
            try:
                p = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stdin=subprocess.PIPE)
                if res:
                    p.stdin.write(res)
                res = p.communicate()[0]
            except OSError:
                print "can not run the command"
                res = ''
        return res

    
monitor = RunCmd()
monitor.run()
