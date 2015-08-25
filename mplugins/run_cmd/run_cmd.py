#!/usr/bin/env python

import sys
import shlex
import subprocess

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL


class RunCmd(MPlugin):
    def run(self):
        cmd = self.config.get('cmd')
        
        result, stdout = self._run_command(cmd)
        if result: result = CRITICAL

        data = metrics = {}
        if self._is_string(stdout):
            data['result_str'] = data
            data['result_num'] = None

        elif self._is_number(stdout):
            data['result_num'] = data
            data['result_str'] = None
            
            # Metric only if is numeric
            metrics = {
              'result': {
                'result': data['result_num']
              }
            }    

        else:
            self.exit(CRITICAL, message="Unsupported result")

        self.exit(result, data, metrics)

    def _run_command(self, cmd):
        commands = cmd.split('|')

        result = stdout = None
        for command in commands:
            try:
                p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                if stdout:
                    p.stdin.write(stdout)
                    
                stdout = p.communicate()[0]
                result = p.wait()

            except OSError:
                self.exit(CRITICAL, message="Unable to run command")
                
        return result, stdout
    
monitor = RunCmd()
monitor.run()
