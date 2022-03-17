#!/usr/bin/env python3

# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import os
import subprocess
from tabnanny import check
import unittest


sanoid_cmd = os.environ.get("SANOID")

def monitor_snapshots_command():
    """Runs sanoid --monitor-snapshots and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-snapshots"], capture_output=True)
    return return_info
    
def run_sanoid_cron_command():
    """Runs sanoid and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--cron", "--verbose"], capture_output=True, check=True)
    return return_info


class TestMonitoringOutput(unittest.TestCase):
    def test_no_zpool(self):
        """Test what happens if there is no zpool at all"""

        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        self.assertEqual(return_info.returncode, 2)

    def test_with_zpool_no_snapshots(self):
        """Test what happens if there is a zpool, but with no snapshots"""

        # Make the zpool
        if not os.environ.get("POOL_TARGET"):
            pool_disk_image = "/zpool.img"
        else:
            subprocess.run(["mkdir", "-p", os.environ.get("POOL_TARGET")], check=True)
            pool_disk_image = os.environ.get("POOL_TARGET") + "/zpool.img"

        subprocess.run(["truncate", "-s", "5120M", pool_disk_image], check=True)
        subprocess.run(["zpool", "create", "-f", os.environ.get("POOL_NAME"), pool_disk_image], check=True)

        # Run sanoid --monitor-snapshots before doing anything else
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        self.assertEqual(return_info.returncode, 2)

        # Run sanoid and test again
        # run_sanoid_cron_command()
        # return_info = monitor_snapshots_command()
        # self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        # self.assertEqual(return_info.returncode, 2)

    #     return_info = monitor_snapshots_command()
    #     self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")


if __name__ == '__main__':
    unittest.main()
