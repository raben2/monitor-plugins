#!/usr/bin/env python

import sys
import subprocess
import shlex

sys.path.append('../../../plugins')

from __mplugin import MPlugin
from __mplugin import OK, CRITICAL


class CheckMySQLSlave(MPlugin):
    def mysql_repchk(self, arg):
        proc = subprocess.Popen(shlex.split(arg),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=False)

        out, err = proc.communicate()
        ret = proc.returncode
        return ret, out, err

    def run(self):
        RETCODE, OUTPUT, ERR = self.mysql_repchk('/usr/bin/mysql \
                --defaults-file=/root/.my.cnf \
                -e "SHOW SLAVE STATUS\\G"')

        if RETCODE:
            self.exit(CRITICAL, message="There was an error (%d): " % RETCODE)

        if OUTPUT != "":
            SHOW_STATUS_LIST = OUTPUT.split('\n')
            del SHOW_STATUS_LIST[0]
            del SHOW_STATUS_LIST[-1]

            SLAVE_STATUS = {}
            for i in SHOW_STATUS_LIST:
                if ":" in i:
                    SLAVE_STATUS[i.split(':')[0].strip()] = i.split(':')[1].strip()

            if SLAVE_STATUS["Slave_IO_Running"] == "Yes" and \
                    SLAVE_STATUS["Slave_SQL_Running"] == "Yes" and \
                    SLAVE_STATUS["Last_Errno"] == "0":

                print "status OK\n" \
                    "metric SLAVE_STATUS string ONLINE\n" \
                    "metric SECONDS_BEHIND_MASTER int " \
                    + SLAVE_STATUS["Seconds_Behind_Master"]
            else:
                print "status OK\n" \
                    "metric SLAVE_STATUS string OFFLINE\n" \
                    "metric SECONDS_BEHIND_MASTER int " \
                    + SLAVE_STATUS["Seconds_Behind_Master"]

        else:
            self.exit(CRITICAL, message="status ERROR: metric SLAVE_STATUS string NOT_CONFIGURED")

if __name__ == '__main__':
    monitor = CheckMySQLSlave()
    monitor.run()




