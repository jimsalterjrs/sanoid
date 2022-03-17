#!/usr/bin/env python3

# this software is licensed for use under the Free Software Foundation's GPL v3.0 license, as retrieved
# from http://www.gnu.org/licenses/gpl-3.0.html on 2014-11-17.  A copy should also be available in this
# project's Git repository at https://github.com/jimsalterjrs/sanoid/blob/master/LICENSE.


import unittest

class TestNothing(unittest.TestCase):
    def test_nothing(self):
        """Test"""

        # Test sanoid_snapshots_exist
        self.assertEqual(1,2)


if __name__ == '__main__':
    unittest.main()
