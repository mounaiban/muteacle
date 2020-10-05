"""
Muteacle Helper Function Test Suite

This test suite verifies the correctness of the helper functions
in the main module

"""
# Copyright © 2020 Moses Chong
#
# This file is part of the Muteacle Shadow Logging System Library (muteacle)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from muteacle import dict_to_json, \
    interval_end, interval_next_common_start, interval_number, \
    interval_seconds_left, interval_start, \
    join_dict
from itertools import combinations

# The following imports are already present in the mutacle_test_repository
# module but are repeated here to make the code clearer.
import unittest
from datetime import datetime, timedelta

class TestDictToJSON(unittest.TestCase):
    """
    Tests for the key-selective ``dict``-to-JSON string helper function

    """
    def test_default_params(self):
        """
        Get JSON string of a ``dict`` using default parameters
        """
        d = {'length':297, 'width':210, 'colour':'pink'}
        expected = '{"length": 297, "width": 210, "colour": "pink"}'
        self.assertEqual(dict_to_json(d), expected)

    def test_all_keys_found(self):
        """
        Get JSON string of a ``dict``, selecting valid keys only
        """
        d = {'length':297, 'width':210, 'colour':'pink'}
        ks = ('length', 'width', 'colour')
        out = dict_to_json(d, keys=ks)
        expected = '{"length": 297, "width": 210, "colour": "pink"}'
        self.assertEqual(out, expected)

    def test_some_keys_found(self):
        """
        Get JSON string of a ``dict``, selecting valid and invalid keys
        """
        d = {'length':297, 'width':210, 'colour':'pink'}
        ks = ('flavour', 'length', 'colour')
        out = dict_to_json(d, keys=ks)
        expected = '{"length": 297, "colour": "pink"}'
        self.assertEqual(out, expected)

    def test_no_keys_found(self):
        """
        Get JSON string of a ``dict``, selecting invalid keys only
        """
        d = {'length':297, 'width':210, 'colour':'pink'}
        ks = ('age', 'sex', 'location')
        out = dict_to_json(d, keys=ks)
        expected = '{}'
        self.assertEqual(out, expected)

    def test_no_keys_specified(self):
        """
        Get JSON string of a ``dict``, selecting no keys
        """
        d = {'length':297, 'width':210, 'colour':'pink'}
        ks = ()
        out = dict_to_json(d, keys=ks)
        expected = '{}'
        self.assertEqual(out, expected)

class TestJoinDict(unittest.TestCase):
    """
    Tests for the dictionary concatenation helper function
    """

    def test_different_keys(self):
        """
        Concatenate two dicts with different keys
        """
        a = {'alfa' : 'almond', 'bravo' : 'brazil'}
        b = {'charlie' : 'cashew', 'delta' : 'donut'}
        expected_result = {
            'alfa' : 'almond',
            'bravo' : 'brazil',
            'charlie' : 'cashew',
            'delta' : 'donut',
        }
        test = join_dict(a, b)
        self.assertEqual(test, expected_result)

    def test_different_keys_same_values(self):
        """
        Concatenate two dicts with the same values under different keys
        """
        a = {'alfa' : 'zebra' , 'bravo' : 'zebra' }
        b = {'charlie' : 'zebra' , 'delta' : 'zebra' }
        expected_result = {
            'alfa' : 'zebra',
            'bravo' : 'zebra',
            'charlie' : 'zebra',
            'delta' : 'zebra',
        }
        test = join_dict(a, b)
        self.assertEqual(test, expected_result)

    def test_same_keys_different_values(self):
        """
        Concatenate two dicts with different values with the same keys
        """
        a = {'alfa' : 'almond', 'bravo' : 'brazil'}
        b = {'alfa' : 'avocado', 'bravo' : 'broccoli'}
        expected_result = {
            'alfa' : ('almond', 'avocado'),
            'bravo' : ('brazil', 'broccoli'),
        } # Left side dict values take precedence
        test = join_dict(a, b)
        self.assertEqual(test, expected_result)

    def test_same_keys_different_values_higher_order(self):
        """
        Concatenate two dicts with different values with the same keys,
        where at least one dict is a result of a previous combination
        """
        a = {
            'alfa' : ('almond', 'avocado'),
            'bravo' : 'brazil'
        }
        b = {
            'alfa' : 'anise',
            'bravo' : ('broccoli', 'bread_crumbs'),
        }
        expected_result = {
            'alfa' : ('almond', 'avocado', 'anise'),
            'bravo' : ('brazil', 'broccoli', 'bread_crumbs')
        }
        test = join_dict(a, b)
        self.assertEqual(test, expected_result)

    def test_combined(self):
        """
        Concatenate two dicts that contain all expected cases
        """
        a = {
            'alfa' : 11,
            'bravo' : 'brazil',
            'charlie' : ('cola', 'cranberry'),
            'delta' : 4,
            'foxtrot' : ( [601, 602], ),
        }
        b = {
            'alfa' : 12,
            'bravo' : ('broccoli', 'bread_crumbs'),
            'charlie' : 'cinnamon',
            'echo' : 5,
            'foxtrot' : ( (691, 692, 693), ),
        }
        expected_result = {
            'alfa' : (11, 12),
            'bravo' : ('brazil', 'broccoli', 'bread_crumbs'),
            'charlie' : ('cola', 'cranberry', 'cinnamon'),
            'delta' : 4,
            'echo' : 5,
            'foxtrot' : ( [601, 602], (691, 692, 693) ),
        }
        test = join_dict(a, b)
        self.assertEqual(test, expected_result)

class TestIntervalNumber(unittest.TestCase):
    """
    Tests for Day Interval Number lookup function
    """
    def test_interval_number_1_second_intervals(self):
        time_res_s = 1
        expected_results = {
            datetime(2020, 12, 25, 0, 0) : 0,
            datetime(2020, 12, 25, 2, 0) : 7200,
            datetime(2020, 12, 25, 4, 0) : 14400,
            datetime(2020, 12, 25, 6, 0) : 21600,
            datetime(2020, 12, 25, 8, 0) : 28800,
            datetime(2020, 12, 25, 10, 0) : 36000,
            datetime(2020, 12, 25, 12, 0) : 43200,
            datetime(2020, 12, 25, 14, 0) : 50400,
            datetime(2020, 12, 25, 16, 0) : 57600,
            datetime(2020, 12, 25, 18, 0) : 64800,
            datetime(2020, 12, 25, 20, 0) : 72000,
            datetime(2020, 12, 25, 22, 0) : 79200,
            datetime(2020, 12, 25, 23, 59, 59) : 86399,
        }
        for k in expected_results.keys():
            with self.subTest(ts=k):
                intvn_out = interval_number(k, time_res_s)
                intvn_expected = expected_results[k]
                self.assertEqual(intvn_out, intvn_expected)

    def test_interval_number_3_hour_intervals(self):
        time_res_s = 10800
        expected_results = {
            datetime(2020, 12, 25, 0, 0) : 0,
            datetime(2020, 12, 25, 3, 0) : 1,
            datetime(2020, 12, 25, 6, 0) : 2,
            datetime(2020, 12, 25, 9, 0) : 3,
            datetime(2020, 12, 25, 12, 0) : 4,
            datetime(2020, 12, 25, 15, 0) : 5,
            datetime(2020, 12, 25, 18, 0) : 6,
            datetime(2020, 12, 25, 21, 0) : 7,
            datetime(2020, 12, 25, 23, 59, 59) : 7,
        }
        for k in expected_results.keys():
            with self.subTest(ts=k):
                intvn_out = interval_number(k, time_res_s)
                intvn_expected = expected_results[k]
                self.assertEqual(intvn_out, intvn_expected)

    def test_interval_number_24_hour_intervals(self):
        time_res_s = 86400
        expected_results = {
            datetime(2020, 12, 25, 0, 0) : 0,
            datetime(2020, 12, 25, 11, 59) : 0,
            datetime(2020, 12, 25, 12, 00) : 0,
            datetime(2020, 12, 25, 23, 59) : 0,
        }
        for k in expected_results.keys():
            with self.subTest(ts=k):
                intvn_out = interval_number(k, time_res_s)
                intvn_expected = expected_results[k]
                self.assertEqual(intvn_out, intvn_expected)

class TestIntervalSecondsLeft(unittest.TestCase):
    """
    Test for Seconds Remaining in Interval function
    """
    # Format: {input : expected_output}
    # Input Format: (datetime, time_res_s)
    # Beware of missing and misplaced brackets
    def test_interval_seconds_left_1_second_intervals(self):
        expected_results = {
            (datetime(2020, 12, 25, 0, 0), 1) : 1,
            (datetime(2020, 12, 25, 0, 0, 0, 500000), 1) : 0.5,
            (datetime(2020, 12, 25, 0, 0, 0, 999999), 1) : 0.000001,
        }
        for k in expected_results.keys():
            with self.subTest(dt=k):
                dt_out = interval_seconds_left(k[0], k[1])
                dt_expected = expected_results[k]
                self.assertEqual(dt_out, dt_expected)

    def test_interval_seconds_left_3_hour_intervals(self):
        expected_results = {
            (datetime(2020, 12, 25, 0, 0), 10800) : 10800,
            (datetime(2020, 12, 25, 1, 30), 10800) : 5400,
            (datetime(2020, 12, 25, 2, 59, 59, 999999), 10800) : 0.000001,
        }
        for k in expected_results.keys():
            with self.subTest(dt=k):
                dt_out = interval_seconds_left(k[0], k[1])
                dt_expected = expected_results[k]
                self.assertEqual(dt_out, dt_expected)

class TestIntervalEnd(unittest.TestCase):
    """
    Test for datetime at end of interval function

    This test case checks all possible values of time_res_s and n,
    as there are only 96 permitted values of time_res_s and the
    number of intervals cannot exceed time_res_s. This test can be
    slow, and may cause the test runner to appear to freeze for
    upwards of tens of seconds.

    """
    # brute-force informal proof
    def test_all_values(self):
        valid_trs = [x for x in range(1,86401) if 86400%x == 0]
        for trs in valid_trs:
            mn = datetime(2020, 12, 25) # midnight xmas 2020
            for n in range(86400//trs):
                # for all intervals...
                with self.subTest(time_res_s=trs, n=n):
                    # ...verify by number of seconds from midnight
                    dt_end = interval_end(mn.year, mn.month, mn.day, trs, n)
                    dt_start = dt_end - timedelta(seconds=trs, microseconds=-1)
                    td = dt_start - mn
                    seconds = td.total_seconds()
                    self.assertEqual(seconds//trs, n)

class TestIntervalStart(unittest.TestCase):
    """
    Test for datetime at start of interval function

    This test case checks all possible values of time_res_s and n,
    as there are only 96 permitted values of time_res_s and the
    number of intervals cannot exceed time_res_s. This test can be
    slow, and may cause the test runner to appear to freeze for
    upwards of tens of seconds.

    """
    def test_all_values(self):
        valid_trs = [x for x in range(1,86401) if 86400%x == 0]
        for trs in valid_trs:
            mn = datetime(2020, 12, 25) # midnight xmas 2020
            for n in range(86400//trs):
                # for all intervals...
                with self.subTest(time_res_s=trs, n=n):
                    # ...verify by number of seconds from midnight
                    dt_start = interval_start(mn.year, mn.month, mn.day, trs, n)
                    td = dt_start - mn
                    seconds = td.total_seconds()
                    self.assertEqual(seconds//trs, n)

class TestNextCommonStart(unittest.TestCase):
    """
    Test for next coincident interval start function

    This test case relies on the correctness of interval_number() and
    interval_start(). All values can be tested, as there are only 96
    permitted values and 4560 permitted combinations for time_res_s.

    """
    def test_all_time_res_s(self):
        valid_values = [x for x in range(1,86401) if 86400%x == 0]
        combs = combinations(valid_values, 2)
        dt = datetime.utcnow()
        for c in combs:
            # combs should contain 2-element tuples with different valid
            # values of time_res_s
            with self.subTest(time_res_s_a=c[0], time_res_s_b=c[1]):
                dt_ns = interval_next_common_start(dt, c[0], c[1])
                na = interval_number(dt_ns, c[0])
                nb = interval_number(dt_ns, c[1])
                dt_ia = interval_start(
                    dt_ns.year, dt_ns.month, dt_ns.day, na, c[0]
                )
                dt_ib = interval_start(
                    dt_ns.year, dt_ns.month, dt_ns.day, nb, c[1]
                )
                self.assertEqual(dt_ia, dt_ns)
                self.assertEqual(dt_ib, dt_ns)
                self.assertGreater(dt_ns, dt)

