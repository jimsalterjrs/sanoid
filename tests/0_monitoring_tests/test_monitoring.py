#!/usr/bin/env python3

# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import os
import subprocess
import unittest


sanoid_cmd = os.environ.get("SANOID")

def monitor_snapshots_command():
    """Runs sanoid --monitor-snapshots and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-snapshots"], capture_output=True)
    return return_info
    


class TestMonitoringOutput(unittest.TestCase):
    def test_no_zpool(self):
        """Test what happens if there is no zpool at all"""

        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, "chicken")


if __name__ == '__main__':
    unittest.main()
