#!/usr/bin/env python3

# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import os
import subprocess
import time
import unittest


sanoid_cmd = os.environ.get("SANOID")
pool_disk_image1 = "/zpool1.img"
pool_name1 = "sanoid-test-1"
pool_disk_image2 = "/zpool2.img"
pool_name2 = "sanoid-test-2"

clk_id = time.CLOCK_REALTIME
starting_time = time.clock_gettime(clk_id)


def monitor_snapshots_command():
    """Runs sanoid --monitor-snapshots and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-snapshots"], capture_output=True)
    return return_info
    
def run_sanoid_cron_command():
    """Runs sanoid and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--cron", "--verbose"], capture_output=True, check=True)
    return return_info

def advance_time(seconds):
    """Advances the system clock by seconds"""
    
    # Get the current time
    clk_id = time.CLOCK_REALTIME
    time_seconds = time.clock_gettime(clk_id)
    # print("Current unix time is", time_seconds, "or", time.asctime(time.gmtime(time_seconds)), "in GMT")
    
    # Set the clock to the current time plus seconds
    time.clock_settime(clk_id, time_seconds + seconds)

    # Print the new time
    time_seconds = time.clock_gettime(clk_id)
    # print("Current unix time is", time_seconds, "or", time.asctime(time.gmtime(time_seconds)), "in GMT")
    return time_seconds


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

        # Clear the snapshot cache in between
        subprocess.run([sanoid_cmd, "--force-update"])

    def tearDown(self):
        """Clean up on either passed or failed tests"""
        subprocess.run(["zpool", "export", pool_name1])
        subprocess.run(["rm", "-f", pool_disk_image1])
        subprocess.run(["zpool", "export", pool_name2])
        subprocess.run(["rm", "-f", pool_disk_image2])
        time.clock_settime(clk_id, starting_time)

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

    def test_one_warning_hourly(self):
        """Test one warning on hourly snapshots, no critical warnings, to check output and error status"""

        run_sanoid_cron_command()
        
        # Advance 100 mins to trigger the hourly warning on sanoid-test-1 but nothing else
        advance_time(100 * 60)
        return_info = monitor_snapshots_command()
        # Output should be something like: 
        # WARN: sanoid-test-1 newest hourly snapshot is 1h 40m 0s old (should be < 1h 30m 0s)\n
        # But we cannot be sure about the exact time as test execution could be different on
        # different machines, so ignore the bits that may be different.
        self.assertEqual(return_info.stdout[:49], b"WARN: sanoid-test-1 newest hourly snapshot is 1h ")
        self.assertEqual(return_info.stdout[-30:], b"s old (should be < 1h 30m 0s)\n")
        self.assertEqual(return_info.returncode, 1)

    def test_two_criticals_hourly(self):
        """Test two criticals (hourly), to check output and error status"""

        run_sanoid_cron_command()
        
        # Advance 390 mins to trigger the hourly critical on both sanoid-test-1 and sanoid-test-2
        advance_time(390 * 60)
        return_info = monitor_snapshots_command()

        # Output should be something like: 
        # CRIT: sanoid-test-1 newest hourly snapshot is 6h 30m 1s old (should be < 6h 0m 0s), CRIT: sanoid-test-2 newest hourly snapshot is 6h 30m 1s old (should be < 6h 0m 0s)\n
        # But we cannot be sure about the exact time as test execution could be different on
        # different machines, so ignore the bits that may be different.
        comma_location = return_info.stdout.find(b",")
        self.assertEqual(return_info.stdout[:49], b"CRIT: sanoid-test-1 newest hourly snapshot is 6h ")
        self.assertEqual(return_info.stdout[comma_location - 28:comma_location], b"s old (should be < 6h 0m 0s)")
        self.assertEqual(return_info.stdout[comma_location:comma_location + 51], b", CRIT: sanoid-test-2 newest hourly snapshot is 6h ")
        self.assertEqual(return_info.stdout[-29:], b"s old (should be < 6h 0m 0s)\n")
        self.assertEqual(return_info.returncode, 2)

    def test_two_warnings_daily(self):
        """Test two warnings (daily), to check output and error status"""

        run_sanoid_cron_command()
        
        # Advance more than 28 hours to trigger the daily warning on both sanoid-test-1 and sanoid-test-2
        advance_time(29 * 60 * 60)
        return_info = monitor_snapshots_command()

        # Output should be something like: 
        # CRIT: sanoid-test-1 newest hourly snapshot is 1d 5h 0m 0s old (should be < 6h 0m 0s), CRIT: sanoid-test-2 newest hourly snapshot is 1d 5h 0m 0s old (should be < 6h 0m 0s), WARN: sanoid-test-1 newest daily snapshot is 1d 5h 0m 0s old (should be < 1d 4h 0m 0s), WARN: sanoid-test-2 newest daily snapshot is 1d 5h 0m 0s old (should be < 1d 4h 0m 0s)\n
        # But we cannot be sure about the exact time as test execution could be different on
        # different machines, so ignore the bits that may be different.
        print(return_info.stdout)
        output_list = return_info.stdout.split(b", ")

        self.assertEqual(output_list[0][:49], b"CRIT: sanoid-test-1 newest hourly snapshot is 1d ")
        self.assertEqual(output_list[0][-28:], b"s old (should be < 6h 0m 0s)")
        self.assertEqual(output_list[1][:49], b"CRIT: sanoid-test-2 newest hourly snapshot is 1d ")
        self.assertEqual(output_list[1][-28:], b"s old (should be < 6h 0m 0s)")
        
        self.assertEqual(output_list[2][:48], b"WARN: sanoid-test-1 newest daily snapshot is 1d ")
        self.assertEqual(output_list[2][-31:], b"s old (should be < 1d 4h 0m 0s)")
        self.assertEqual(output_list[3][:48], b"WARN: sanoid-test-2 newest daily snapshot is 1d ")
        self.assertEqual(output_list[3][-32:], b"s old (should be < 1d 4h 0m 0s)\n")

        self.assertEqual(return_info.returncode, 2)


if __name__ == '__main__':
    unittest.main()
