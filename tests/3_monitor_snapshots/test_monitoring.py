#!/usr/bin/env python3
# (c) 2022 Aaron Whitehouse <code@whitehouse.kiwi.nz>
# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import json
import os
import subprocess
import time
import unittest

SANOID_TEST_1_HOURLY_WARN = 90 * 60            # 90m
SANOID_TEST_1_HOURLY_CRIT = 360 * 60            # 360m
SANOID_TEST_1_DAILY_WARN = 28 * 60 * 60         # 28h
SANOID_TEST_1_DAILY_CRIT = 32 * 60 * 60         # 32h
SANOID_TEST_1_MONTHLY_WARN = 32 * 24 * 60 * 60  # 32d
SANOID_TEST_1_MONTHLY_CRIT = 40 * 24 * 60 * 60  # 40d

SANOID_TEST_2_HOURLY_WARN = 290 * 60            # 290m
SANOID_TEST_2_HOURLY_CRIT = 360 * 60            # 360m
SANOID_TEST_2_DAILY_WARN = 28 * 60 * 60         # 28h
SANOID_TEST_2_DAILY_CRIT = 48 * 60 * 60         # 48h
SANOID_TEST_2_MONTHLY_WARN = 32 * 24 * 60 * 60  # 32d
SANOID_TEST_2_MONTHLY_CRIT = 40 * 24 * 60 * 60  # 40d


sanoid_cmd = os.environ.get("SANOID")
pool_disk_image1 = "/zpool1.img"
pool_name1 = "sanoid-test-1"
pool_disk_image2 = "/zpool2.img"
pool_name2 = "sanoid-test-2"

clk_id = time.CLOCK_REALTIME
starting_time = time.clock_gettime(clk_id)


def get_sanoid_json():
    """Runs sanoid --monitor-metrics-json and returns the snapshot component of the JSON"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-metrics-json"], capture_output=True, check=True)
    # print(return_info.stdout)
    sanoid_metrics = json.loads(return_info.stdout)
    return sanoid_metrics

def monitor_snapshots_command():
    """Runs sanoid --monitor-snapshots and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-snapshots"], capture_output=True)
    return return_info

def monitor_metrics_json_command():
    """Runs sanoid --monitor-metrics-json and returns a CompletedProcess instance"""
    return_info = subprocess.run([sanoid_cmd,  "--monitor-metrics-json"], capture_output=True, check=True)
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

        # Test regular (Nagios) output
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        
        nagios_return_code = return_info.returncode
        self.assertEqual(nagios_return_code, 2)

        sanoid_json = get_sanoid_json()
        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]
        
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"], SANOID_TEST_1_HOURLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 2)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"], SANOID_TEST_1_HOURLY_WARN) 

        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"], SANOID_TEST_1_DAILY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 2)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"], SANOID_TEST_1_DAILY_WARN)

        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"], SANOID_TEST_1_MONTHLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 2)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"], SANOID_TEST_1_MONTHLY_WARN)
        

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

    def _check_parts_from_sanoid_conf(self, snapshot_json):
        """Checks the parts of the JSON from sanoid.conf (which should always be the same)"""
        # sanoid-test-1 hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"], SANOID_TEST_1_HOURLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"], SANOID_TEST_1_HOURLY_WARN) 

        # sanoid-test-1 daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"], SANOID_TEST_1_DAILY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"], SANOID_TEST_1_DAILY_WARN)

        # sanoid-test-1 monthly
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"], SANOID_TEST_1_MONTHLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"], SANOID_TEST_1_MONTHLY_WARN)    

        # sanoid-test-2 hourly
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["crit_age_seconds"], SANOID_TEST_2_HOURLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["warn_age_seconds"], SANOID_TEST_2_HOURLY_WARN) 

        # sanoid-test-2 daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["crit_age_seconds"], SANOID_TEST_2_DAILY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["warn_age_seconds"], SANOID_TEST_2_DAILY_WARN)

        # sanoid-test-2 monthly
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["crit_age_seconds"], SANOID_TEST_2_MONTHLY_CRIT)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["monitor_dont_crit"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["monitor_dont_warn"], 0)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["warn_age_seconds"], SANOID_TEST_2_MONTHLY_WARN)    

    def test_with_zpool_no_snapshots(self):
        """Test what happens if there is a zpool, but with no snapshots"""

        # Run sanoid --monitor-snapshots before doing anything else
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"CRIT: sanoid-test-1 has no daily snapshots at all!, CRIT: sanoid-test-1 has no hourly snapshots at all!, CRIT: sanoid-test-1 has no monthly snapshots at all!, CRIT: sanoid-test-2 has no daily snapshots at all!, CRIT: sanoid-test-2 has no hourly snapshots at all!, CRIT: sanoid-test-2 has no monthly snapshots at all!\n")
        nagios_return_code = return_info.returncode
        self.assertEqual(nagios_return_code, 2)

        sanoid_json = get_sanoid_json()
        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]
        
        self._check_parts_from_sanoid_conf(snapshot_json)

        # Output matches the above test_no_zpool
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 2)

        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 2)

        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 0)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 2)

    def test_immediately_after_running_sanoid(self):
        """Test immediately after running sanoid --cron"""

        run_sanoid_cron_command()
        return_info = monitor_snapshots_command()
        self.assertEqual(return_info.stdout, b"OK: all monitored datasets (sanoid-test-1, sanoid-test-2) have fresh snapshots\n")
        nagios_return_code = return_info.returncode
        self.assertEqual(nagios_return_code, 0)

        sanoid_json = get_sanoid_json()
        unix_time_now = time.time()

        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]

        self._check_parts_from_sanoid_conf(snapshot_json)

        # sanoid-test-1 hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["hourly"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)

        # sanoid-test-1 daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)        

        # sanoid-test-1 monthly
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)

        # sanoid-test-2 hourly
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["hourly"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)

        # sanoid-test-2 daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)        

        # sanoid-test-2 monthly
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should only be a second or two, as the snapshot has just been created
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now, delta=600)

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
        nagios_return_code = return_info.returncode
        self.assertEqual(nagios_return_code, 1)

        sanoid_json = get_sanoid_json()
        unix_time_now = time.time()

        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]

        self._check_parts_from_sanoid_conf(snapshot_json)

        # sanoid-test-1 hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 1)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], (600 * 100) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["hourly"]['newest_snapshot_ctime_seconds'], (unix_time_now - (60 * 100)), delta=600)

        # We should have a warning on the hourly (but not a critical)
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 1)
        self.assertGreater(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"])
        
        # sanoid-test-1 daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], 6600)
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now - (60 * 100), delta=600)        

        # sanoid-test-1 monthly
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], 6600)
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (60 * 100), delta=600)

        # sanoid-test-2 hourly
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], 6600)
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["hourly"]['newest_snapshot_ctime_seconds'], unix_time_now - (60 * 100), delta=600)

        # sanoid-test-2 daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], 6600)
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now  - (60 * 100), delta=600)        

        # sanoid-test-2 monthly
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 6000, as we advanced time 100 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], 6600)
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (60 * 100), delta=600)


    def test_two_criticals_hourly(self):
        """Test two criticals (hourly), to check output and error status"""

        run_sanoid_cron_command()
        
        # Advance 390 mins to trigger the hourly critical on both sanoid-test-1 and sanoid-test-2
        advance_time(390 * 60)
        return_info = monitor_snapshots_command()
        nagios_return_code = return_info.returncode

        # Output should be something like: 
        # CRIT: sanoid-test-1 newest hourly snapshot is 6h 30m 1s old (should be < 6h 0m 0s), CRIT: sanoid-test-2 newest hourly snapshot is 6h 30m 1s old (should be < 6h 0m 0s)\n
        # But we cannot be sure about the exact time as test execution could be different on
        # different machines, so ignore the bits that may be different.
        comma_location = return_info.stdout.find(b",")
        self.assertEqual(return_info.stdout[:49], b"CRIT: sanoid-test-1 newest hourly snapshot is 6h ")
        self.assertEqual(return_info.stdout[comma_location - 28:comma_location], b"s old (should be < 6h 0m 0s)")
        self.assertEqual(return_info.stdout[comma_location:comma_location + 51], b", CRIT: sanoid-test-2 newest hourly snapshot is 6h ")
        self.assertEqual(return_info.stdout[-29:], b"s old (should be < 6h 0m 0s)\n")
        self.assertEqual(nagios_return_code, 2)

        sanoid_json = get_sanoid_json()
        unix_time_now = time.time()

        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]
        self._check_parts_from_sanoid_conf(snapshot_json)

        # sanoid-test-1 hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 1)

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["hourly"]['newest_snapshot_ctime_seconds'], (unix_time_now - (390 * 60)), delta=600)

        # We should have a critical on the hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 2)
        self.assertGreater(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"])
        self.assertGreater(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"])
        
        # sanoid-test-1 daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now - (390 * 60), delta=600)        

        # sanoid-test-1 monthly
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (390 * 60), delta=600)

        # sanoid-test-2 hourly        
        # We should have a critical on the hourly
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["snapshot_health_issues"], 2)
        self.assertGreater(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["warn_age_seconds"])
        self.assertGreater(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["crit_age_seconds"])

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["hourly"]['newest_snapshot_ctime_seconds'], unix_time_now - (390 * 60), delta=600)

        # sanoid-test-2 daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now  - (390 * 60), delta=600)        

        # sanoid-test-2 monthly
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 23400 (390 * 60), as we advanced time 390 minutes
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], (390 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (390 * 60), delta=600)


    def test_two_criticals_hourly_two_warnings_daily(self):
        """Test two criticals (hourly) and two warnings (daily), to check output and error status"""

        run_sanoid_cron_command()
        
        # Advance more than 28 hours to trigger the daily warning on both sanoid-test-1 and sanoid-test-2
        advance_time(29 * 60 * 60)
        return_info = monitor_snapshots_command()
        nagios_return_code = return_info.returncode

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

        self.assertEqual(nagios_return_code, 2)

        sanoid_json = get_sanoid_json()
        unix_time_now = time.time()

        self.assertEqual(sanoid_json["overall_snapshot_health_issues"], nagios_return_code)

        snapshot_json = sanoid_json["snapshot_info"]
        self._check_parts_from_sanoid_conf(snapshot_json)

        # sanoid-test-1 hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["has_snapshots"], 1)

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["hourly"]['newest_snapshot_ctime_seconds'], (unix_time_now - (29 * 60 * 60)), delta=600)

        # We should have a critical on the hourly
        self.assertEqual(snapshot_json["sanoid-test-1"]["hourly"]["snapshot_health_issues"], 2)
        self.assertGreater(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["warn_age_seconds"])
        self.assertGreater(snapshot_json["sanoid-test-1"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["hourly"]["crit_age_seconds"])
        
        # sanoid-test-1 daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["has_snapshots"], 1)

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now - (29 * 60 * 60), delta=600)        

        # We should have a warning (but not a critical) on the daily
        self.assertEqual(snapshot_json["sanoid-test-1"]["daily"]["snapshot_health_issues"], 1)
        self.assertGreater(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["daily"]["crit_age_seconds"])

        # sanoid-test-1 monthly
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-1"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-1"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-1"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-1"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (29 * 60 * 60), delta=600)

        # sanoid-test-2 hourly        
        # We should have a critical on the hourly
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["hourly"]["snapshot_health_issues"], 2)
        self.assertGreater(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["warn_age_seconds"])
        self.assertGreater(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["hourly"]["crit_age_seconds"])

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-2"]["hourly"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["hourly"]['newest_snapshot_ctime_seconds'], unix_time_now - (29 * 60 * 60), delta=600)

        # sanoid-test-2 daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["has_snapshots"], 1)

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["daily"]['newest_snapshot_ctime_seconds'], unix_time_now  - (29 * 60 * 60), delta=600)      
        
        # We should have a warning (but not a critical) on the daily
        self.assertEqual(snapshot_json["sanoid-test-2"]["daily"]["snapshot_health_issues"], 1)
        self.assertGreater(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["daily"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["daily"]["crit_age_seconds"])
  
        # 'monthly': {'newest_age_seconds': 104400, 'newest_snapshot_ctime_seconds': 1659643155}, 
        # sanoid-test-2 monthly
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["has_snapshots"], 1)
        self.assertEqual(snapshot_json["sanoid-test-2"]["monthly"]["snapshot_health_issues"], 0)

        # newest_age_seconds should be approximately 104400 (29 * 60 * 60), as we advanced time 29 hours
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], (29 * 60 * 60) + 600)
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["warn_age_seconds"])
        self.assertLess(snapshot_json["sanoid-test-2"]["monthly"]["newest_age_seconds"], snapshot_json["sanoid-test-2"]["monthly"]["crit_age_seconds"])
        self.assertAlmostEqual(snapshot_json["sanoid-test-2"]["monthly"]['newest_snapshot_ctime_seconds'], unix_time_now - (29 * 60 * 60), delta=600)


if __name__ == '__main__':
    unittest.main()
