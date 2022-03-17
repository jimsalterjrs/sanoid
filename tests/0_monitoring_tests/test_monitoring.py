#!/usr/bin/env python3

# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import os
import subprocess
from tabnanny import check
import unittest


sanoid_cmd = os.environ.get("SANOID")
pool_disk_image1 = "/zpool1.img"
pool_name1 = "sanoid-test-1"
pool_disk_image2 = "/zpool2.img"
pool_name2 = "sanoid-test-2"


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

class TestsWithZpool(unittest.TestCase):
    """Tests that require a test zpool"""

    def setUp(self):
        """Set up the zpool"""
        subprocess.run(["truncate", "-s", "512M", pool_disk_image1], check=True)
        subprocess.run(["zpool", "create", "-f", pool_name1, pool_disk_image1], check=True)

        subprocess.run(["truncate", "-s", "512M", pool_disk_image2], check=True)
        subprocess.run(["zpool", "create", "-f", pool_name2, pool_disk_image2], check=True)

    def tearDown(self):
        """Clean up on either passed or failed tests"""
        subprocess.run(["zpool", "export", pool_name1])
        subprocess.run(["rm", pool_disk_image1])
        subprocess.run(["zpool", "export", pool_name2])
        subprocess.run(["rm", pool_disk_image2])

    def test_with_zpool_no_snapshots(self):
        """Test what happens if there is a zpool, but with no snapshots"""

        # Run sanoid --monitor-snapshots before doing anything else
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        self.assertEqual(return_info.returncode, 2)

    def test_immediately_after_running_sanoid(self):
        """Test immediately after running sanoid --cron"""

        run_sanoid_cron_command()
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"OK: all monitored datasets (sanoid-test-1, sanoid-test-2) have fresh snapshots\n")
        self.assertEqual(return_info.returncode, 0)


if __name__ == '__main__':
    unittest.main()
