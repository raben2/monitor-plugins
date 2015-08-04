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

        result = self._run_command(cmd)
        data = {}

        if not result:
            self.exit(CRITICAL, message="Empty output from the command")

        if isinstance(data, str):
            data['result_str'] = data
            data['result_num'] = None
        elif isinstance(data, int) or isinstance(data, float):
            data['result_num'] = data
            data['result_str'] = None
        else:
            self.exit(CRITICAL, message="Unsupported opera")
        metrics = {
            'result': {
                'result_str': data['result_str'],
                'result_num':data['result_num']

                }
            }
        self.exit(OK, data, metrics)

    def _run_command(self, cmd):
        commands = cmd.split('|')
        res = None
        for command in commands:
            try:
                p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                if res:
                    p.stdin.write(res)
                res = p.communicate()[0]
            except OSError:
                self.exit(CRITICAL, message="Unable to run command")
        return res

    
monitor = RunCmd()
monitor.run()
