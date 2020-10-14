"""
Muteacle Repository Master Test Suite

This test suite verifies the basic functionality of Repository
classes that is common to all implementations. The suite excludes
implementation-specific tests.

Notes
-----
This module is named to avoid detection by Python's unittest
system under the default test detection behaviour as the suite
is not designed to test Repository classes as an instance.

To implement tests, create new subclasses from the test case classes
in this module for each Repository subclass, overriding class
attributes as required. The tests herein will be executed using the
Repository subclass. Add Repository subclass-specific tests as
necessary to the test subclass.

Please avoid overriding any method in this module without a
sufficiently compelling reason. Tests that are specific to any
Repository subclass should be implemented in separate methods of
subclassed test cases/suites.

For an implementation example, see the module ``tests_sqlite``.

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

import unittest
import muteacle
import json

# The following imports are already present in the mutacle_test_repository
# module but are repeated here to make the code clearer.
from datetime import datetime, timedelta
from secrets import token_bytes

# Test Cases

class SetupTests(unittest.TestCase):
    """
    Tests to verify the correctness of Hasher and Repository
    configuration loading, and saving.

    Attributes
    ==========
    Please override the following class attributes as necessary
    when implementing a test for a Repository class:

    * repository_class - the Repository subclass you are testing.
      All tests in this class will be executed using an instance
      of repository_class

    * hasher_kwargs - keyword arguments to be passed to new hashers
      by default

    * repo_kwargs - keyword arguments to be passed to new repository
      instances by default

    """
    repository_class = muteacle.Repository
    hasher_kwargs = {}
    repo_kwargs = {}

    # NOTE: Tests are to be arranged by type (Setup then Logging),
    # then alphabetically (a-z)

    def setUp(self):
        self.repo = self.repository_class(**self.repo_kwargs)

    def tearDown(self):
        # set repository to end-of-test config to avoid confusing
        # subsequent runs if tests are run on persistent/storage memory
        meta = {
            'dt': datetime.utcnow().timestamp(),
            'test_suite_ended': 'RepositorySetupTests'
        }
        time_res_s = self.repo_kwargs['time_res_s']
        self.repo.set_config({'meta': meta, 'time_res_s': time_res_s})
        muteacle.sleep_until_interval_end(time_res_s)

    def test_set_config(self):
        """
        Repository: config change request test
        The new configuration must be staged correctly during the
        wait before applying it.

        """
        meta = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config'
        }
        config_orig = self.repo.get_config()
        self.repo.set_config({'meta': meta})
        config_sched = self.repo.pending_repo_config()

        self.assertEqual(config_sched['meta'], meta)
        # verify that unchanged config values are intact
        keys = [k for k in self.repo.set_config_keys if k != 'meta']
        for k in keys:
            self.assertEqual(config_orig[k], config_sched[k])

    def test_set_config_applied(self):
        """
        Repository: config change request test
        The new configuration must be applied correctly after the
        waiting period is past

        """
        meta = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_applied',
        }
        config_orig = self.repo.get_config()
        self.repo.set_config({'meta': meta})
        config_sched = self.repo.pending_repo_config()
        # PROTIP: wait until the repo config applies
        while self.repo.pending_repo_config_datetime() is not None:
            pass
            # TODO: replace this waiting loop with a more
            # power-efficient routine
        config_app = self.repo.get_config()

        self.assertEqual(config_sched, config_app)
        self.assertEqual(config_app['meta'], meta)
        # verify that unchanged config values are intact
        keys = [k for k in self.repo.set_config_keys if k != 'meta']
        for k in keys:
            self.assertEqual(config_app[k], config_orig[k])

    def test_set_config_change_pending(self):
        """
        Repository: pending config replacement test
        Changes to pending configurations before they are applied
        must be correctly accounted for

        """
        meta_a = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_pending_applied',
            'action': 'set_config_a',
        }
        meta_b = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_pending_applied',
            'action': 'set_config_b',
        }

        config_orig = self.repo.get_config()
        self.repo.set_config({'meta': meta_a})
        self.repo.set_config({'meta': meta_b})
        config_presched = self.repo.pending_repo_config()

        self.assertEqual(config_presched['meta'], meta_b)
        # verify that unchanged config values are intact
        keys = [k for k in self.repo.set_config_keys if k != 'meta']
        for k in keys:
            self.assertEqual(config_presched[k], config_orig[k])

    def test_set_config_change_pending_applied(self):
        """
        Repository: config change request /w change to config before applying
        Changes to pending configuration must be correctly applied
        once the waiting period is past

        """
        meta_a = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_pending_applied',
            'action': 'set_config_a',
        }
        meta_b = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_pending_applied',
            'action': 'set_config_b',
        }

        config_orig = self.repo.get_config()
        self.repo.set_config({'meta': meta_a})
        self.repo.set_config({'meta': meta_b})
        config_presched = self.repo.pending_repo_config()
        muteacle.sleep_until_interval_end(config_orig['time_res_s'])
        config_app = self.repo.get_config()
        config_postsched = self.repo.pending_repo_config()

        self.assertEqual(config_postsched, {})
        self.assertEqual(config_app, config_presched)
        # verify that unchanged config values are intact
        keys = [k for k in self.repo.set_config_keys if k != 'meta']
        for k in keys:
            self.assertEqual(config_app[k], config_orig[k])

    def test_set_config_change_pending_cancelled(self):
        """
        Repository: config change request cancellation
        Existing repository configuration must be correctly preserved
        if a configuration change request is cancelled

        """
        meta_x = { 'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_pending_cancelled',
            'action': 'set_pending_config',
        }
        config_orig = self.repo.get_config()

        self.repo.set_config({'meta': meta_x})
        self.repo.set_config(config_orig)
        muteacle.sleep_until_interval_end(config_orig['time_res_s'])
        config_app = self.repo.get_config()

        self.assertEqual(config_app, config_orig)

    def test_set_config_change_nofx_applied(self):
        """
        Repository: ineffective config change
        Existing repository configuration must be correctly preserved
        if a configuration change effectively results in no changes

        """
        meta_x = {
            'dt': datetime.utcnow().timestamp(),
            'test': 'set_config_change_nofx_applied',
            'action': 'set_pending_config',
        }
        config_orig = self.repo.get_config()

        self.repo.set_config(config_orig)
        muteacle.sleep_until_interval_end(config_orig['time_res_s'])
        config_app = self.repo.get_config()

        self.assertEqual(config_app, config_orig)

    def test_load_repo_configs_not_found_past_dt(self):
        """
        Repository: loading configs using datetime before first saved config
        No configurations should be returned if a datetime
        provided points to a time before the start of the interval
        of the first configuration.

        """
        # NOTE: Test will fail if run on persistent storage and
        # tables are not cleared out within 10 years of the first run
        ts = datetime.utcnow().timestamp()
        meta = {'test':'load_repo_config_not_found_past_dt', 'ts':ts}

        self.repo.set_config({'meta':meta})
        dt = datetime.utcnow() - timedelta(days=3650) # ten years ago
        configs = self.repo.load_repo_configs(dt)

        self.assertEqual(configs, [])

    def test_save_hasher_config(self):
        """
        Hasher: high-level hasher configuration write test
        Repository must correctly write Hasher configuration to the
        database when the save_hasher_config() method is used.

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test': 'save_hasher_config', 'ts': ts}
        self.repo.set_config({'meta': meta})

        class_name = self.repo.defaults['hasher_class_name']
        hasher_class = self.repo.supported_hashers[class_name]
        salt_len = self.repo._config['salt_length']
        salt = token_bytes(salt_len)
        hasher_new = hasher_class(salt, meta=meta)
        dt = self.repo.save_hasher_config(hasher_new)

        load = self.repo.get_hashers(dt)
        self.assertIn(hasher_new, load)

    def test_get_hashers_interval_start(self):
        """
        Hasher: load hashers specifying datetime at start of interval

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test': 'get_hashers_interval_start', 'ts': ts}
        time_res_s = self.repo._config['time_res_s']

        muteacle.sleep_until_interval_end(time_res_s)
        req = self.repo.new_hasher(config={'meta': meta})
        hasher = req['hasher']
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        dt_load = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n
        )
        hashers_loaded = self.repo.get_hashers(dt_load)

        self.assertIn(hasher, hashers_loaded)

    def test_get_hashers_interval_end(self):
        """
        Hasher: load hashers specifying datetime at end of interval

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test':'get_hashers_interval_end', 'ts':ts}
        time_res_s = self.repo._config['time_res_s']

        muteacle.sleep_until_interval_end(time_res_s)
        req = self.repo.new_hasher(config={'meta': meta})
        hasher = req['hasher']
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        dt_end = muteacle.interval_end(dt.year, dt.month, dt.day, time_res_s, n)
        hashers_loaded = self.repo.get_hashers(dt_end)

        self.assertIn(hasher, hashers_loaded)

    def test_new_hasher(self):
        """
        Hasher: request new hasher

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test':'new_hasher', 'ts':ts}
        default_class_name = self.repo.defaults['hasher_class_name']
        req = self.repo.new_hasher(config={'meta': meta})
        hasher = req['hasher']
        dt = datetime.utcnow()
        # NOTE: dt is taken slightly after the new hasher request to
        # verify that hashers can still be loaded by specifying any
        # datetime until the end of the same interval.

        hashers_same_dt = self.repo.get_hashers(dt)

        self.assertEqual(hasher.__class__.__name__, default_class_name)
        self.assertIn(hasher, hashers_same_dt)

    def test_new_hasher_class_config_changed(self):
        """
        Hasher: request new hasher with class and configuration change
        Repository must save a new Hasher if it is of a different class
        than the last requested Hasher. The previous Hasher must still be
        retrievable if it was created within the same interval.

        """
        # NOTE: A change in class also causes a change in configuration
        # at time of writing, as all available classes have very different
        # configurables
        ts = datetime.utcnow().timestamp()
        meta = {'test':'new_hasher_class_config_changed','ts_start':ts}
        default_class_name = self.repo.defaults['hasher_class_name']
        class_custom = muteacle.PBKDF2Hasher

        req_a = self.repo.new_hasher(
            hasher_class=class_custom,config={'meta': meta}
        )
        hasher_a = req_a['hasher']
        dt = req_a['datetime']
        req_b = self.repo.new_hasher() # gets a default hasher
        hasher_b = req_b['hasher']

        hashers_same_dt = self.repo.get_hashers(dt)

        self.assertIn(hasher_a, hashers_same_dt)
        self.assertIn(hasher_b, hashers_same_dt)
        self.assertNotEqual(hasher_a.__class__.__name__, default_class_name)

    def test_new_hasher_second_hasher_config_changed(self):
        """
        Hasher: request new hasher with configuration change only
        Repository must save the new Hasher if its configuration has
        changed from the last, despite belonging to the same class.
        The last Hasher must still be retrievable if both hashers were
        created within the same interval.

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test':'new_hasher_class_changed','ts_start':ts}
        cfg_a = {'keylen': 384, 'meta': meta}
        cfg_b = {'keylen': 512, 'meta': meta}

        req_a = self.repo.new_hasher(config=cfg_a)
        hasher_a = req_a['hasher']
        req_b = self.repo.new_hasher(config=cfg_b)
        hasher_b = req_b['hasher']
        dt = req_b['datetime']
        hashers = self.repo.get_hashers(dt)

        self.assertIn(hasher_a, hashers)
        self.assertIn(hasher_b, hashers)

    def test_new_hasher_third_hasher_config_reverted(self):
        """
        Hasher: request new hashers with config change followed by revert
        Repository must correctly save new Hashers if a Hasher
        configuration was requested. If a return to a previous
        configuration is requested thereafter, a new Hasher must be
        created with a new salt.

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test': 'hasher_third_config_reverted', 'ts_start': ts}
        cfg = {'meta': meta}
        class_a = self.repo.supported_hashers['PBKDF2Hasher']
        class_b = self.repo.supported_hashers['ScryptHasher']
        time_res_s = self.repo.get_config()['time_res_s']
        muteacle.sleep_until_interval_end(time_res_s)

        req_a = self.repo.new_hasher(hasher_class=class_a, config=cfg)
        hasher_a = req_a['hasher']
        dt = req_a['datetime']
        req_b = self.repo.new_hasher(hasher_class=class_b, config=cfg)
        hasher_b = req_b['hasher']
        req_c = self.repo.new_hasher(hasher_class=class_a, config=cfg)
        hasher_c = req_c['hasher']
        hashers = self.repo.get_hashers(dt)

        self.assertIn(hasher_a, hashers)
        self.assertIn(hasher_b, hashers)
        self.assertIn(hasher_c, hashers)
        self.assertNotEqual(hasher_a.salt, hasher_c.salt)

    def test_new_hasher_interval_lapsed(self):
        """
        Hasher: request new hasher after interval lapses
        Repository must save a new Hasher if a new one is requested
        after the interval has lapsed, even if the configuration and
        class has not changed in the meantime. Hashers must not be
        retrievable using a datetime from a different interval.

        """
        ts = datetime.utcnow().timestamp()
        test_name = 'new_hasher_interval_passed'
        time_res_s = self.repo.get_config()['time_res_s']
        muteacle.sleep_until_interval_end(time_res_s)

        # first hasher
        meta_a = {'test':test_name, 'ts_start':ts, 'order':1}
        req_a = self.repo.new_hasher(config={'meta':meta_a})
        hasher_a = req_a['hasher']
        dt_a = req_a['datetime']
        load_a = self.repo.get_hashers(dt_a)
        muteacle.sleep_until_interval_end(time_res_s)
        # second hasher
        meta_b = {'test':test_name, 'ts_start':ts, 'order':2}
        req_b = self.repo.new_hasher(config={'meta':meta_b})
        hasher_b = req_b['hasher']
        dt_b = req_b['datetime']
        load_b = self.repo.get_hashers(dt_b)
        muteacle.sleep_until_interval_end(time_res_s)
        # third hasher
        meta_c = {'test':test_name, 'ts_start':ts, 'order':3}
        req_c = self.repo.new_hasher(config={'meta':meta_c})
        hasher_c = req_c['hasher']
        dt_c = req_c['datetime']
        load_c = self.repo.get_hashers(dt_c)
        muteacle.sleep_until_interval_end(time_res_s)

        self.assertNotIn(hasher_a, load_b)
        self.assertNotIn(hasher_a, load_c)
        self.assertNotIn(hasher_b, load_a)
        self.assertNotIn(hasher_b, load_c)
        self.assertNotIn(hasher_c, load_a)
        self.assertNotIn(hasher_c, load_b)
        self.assertIn(hasher_a, load_a)
        self.assertIn(hasher_b, load_b)
        self.assertIn(hasher_c, load_c)
        self.assertEqual(len(load_a), 1)
        self.assertEqual(len(load_b), 1)
        self.assertEqual(len(load_c), 1)

class RepositoryLoggingTests(unittest.TestCase):
    """
    Tests to verify correctness of hash logging and checking
    methods of Repository classes.

    Attributes
    ==========
    Please override the following class attributes as necessary
    when implementing a test for a Repository class:

    * repository_class - the Repository subclass you are testing

    * hasher_class - the Hasher class to be used during testing

    * hasher_kwargs - keyword arguments to be passed to the test
      hashers

    * repo_kwargs - keyword arguments to be passed to new repository
      instances by default

    """
    repository_class = muteacle.Repository
    hasher_class = muteacle.PBKDF2Hasher
    hasher_kwargs = {}
    repo_kwargs = {}

    def get_logging_test_data(self):
        """
        Return time-stamped test data.

        Returns a tuple of byte arrays with test data, with a
        timestamp indicating the time this method was used.

        """
        self.ts_str = str(datetime.utcnow().timestamp())
        data = (
            bytes('alfa_'+self.ts_str, 'utf-8'),
            bytes('bravo_'+self.ts_str, 'utf-8'),
            bytes('charlie_'+self.ts_str, 'utf-8'),
        )
        return data

    def setUp(self):
        self.ts_str = str(datetime.utcnow().timestamp())
        self.repo = self.repository_class(**self.repo_kwargs)
        self.data = (
            bytes('alfa_'+self.ts_str, 'utf-8'),
            bytes('bravo_'+self.ts_str, 'utf-8'),
            bytes('charlie_'+self.ts_str, 'utf-8'),
        )
        self.item_skipped = b'item_skipped'
        self.time_res_s = self.repo._config['time_res_s']

    def test_hash_found_interval_end(self):
        """
        Log: check existing hash specifying end-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )

        dt = req['datetime']
        n = muteacle.interval_number(dt, time_res_s)
        intv_end = muteacle.interval_end(
            dt.year, dt.month, dt.day, time_res_s, n
        )

        for i in data:
            with self.subTest(intv_end=intv_end, item=i):
                result = self.repo.check_log(intv_end, i)
                self.assertTrue(result)

    def test_hash_found_interval_mid(self):
        """
        Log: check existing hash specifying middle-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_start = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n
        )
        intv_mid = intv_start + timedelta(seconds=time_res_s/2)

        for i in data:
            with self.subTest(intv_mid=intv_mid, item=i):
                result = self.repo.check_log(intv_mid, i)
                self.assertTrue(result)

    def test_hash_found_interval_mid_class_change(self):
        """
        Log: check existing hash using mid-interval datetime
        Hashes must remain verifiable across changes in hasher
        configuration.

        """
        time_res_s = self.repo._config['time_res_s']
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_class=self.repo.supported_hashers['ScryptHasher'],
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']

        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_class=self.repo.supported_hashers['PBKDF2Hasher'],
            hasher_config=self.hasher_kwargs
        )

        n = muteacle.interval_number(dt_a, time_res_s)
        intv_mid = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s, n
        )

        for i in data_a:
            with self.subTest(intv_mid=intv_mid, item=i):
                result = self.repo.check_log(intv_mid, i)
                self.assertTrue(result)

        for i in data_b:
            with self.subTest(intv_mid=intv_mid, item=i):
                result = self.repo.check_log(intv_mid, i)
                self.assertTrue(result)

    def test_hash_found_interval_mid_trs_downgrade(self):
        """
        Log: check existing hash using mid-interval datetime /w trs downgrade
        Hashes must be verifiable despite a change in the time_res_s
        setting on the Repository. This test verifies hash recall
        across downgrades of time_res_s (increasing time_res_s causes a
        lower time resolution)

        """
        time_res_s_a = 1
        self.repo.set_config({'time_res_s': time_res_s_a})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']
        n_a = muteacle.interval_number(dt_a, time_res_s_a)
        int_mid_a = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_a, n_a
        )

        time_res_s_b = 2
        self.repo.set_config({'time_res_s': time_res_s_b})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_b = req_b['datetime']
        n_b = muteacle.interval_number(dt_b, time_res_s_b)
        int_mid_b = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_b, n_b
        )

        for i in data_a:
            with self.subTest(intv_mid=int_mid_a, item=i):
                result = self.repo.check_log(int_mid_a, i)
                self.assertTrue(result)

        for i in data_b:
            with self.subTest(intv_mid=int_mid_b, item=i):
                result = self.repo.check_log(int_mid_b, i)
                self.assertTrue(result)

        # TODO: reset time_res_s
        self.repo.set_config(self.repo_kwargs)
        while self.repo.pending_repo_config_datetime() is not None:
            pass

    def test_hash_found_interval_mid_trs_upgrade(self):
        """
        Log: check existing hash using mid-interval datetime /w trs upgrade
        Hashes must be verifiable despite a change in the time_res_s
        setting on the Repository. This test verifies hash recall
        across upgrades of time_res_s (reducing time_res_s causes a
        lower time resolution)

        """
        time_res_s_a = 2
        self.repo.set_config({'time_res_s': time_res_s_a})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']
        n_a = muteacle.interval_number(dt_a, time_res_s_a)
        int_mid_a = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_a, n_a
        )

        time_res_s_b = 1
        self.repo.set_config({'time_res_s': time_res_s_b})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_b = req_b['datetime']
        n_b = muteacle.interval_number(dt_b, time_res_s_b)
        int_mid_b = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_b, n_b
        )

        for i in data_a:
            with self.subTest(intv_mid=int_mid_a, item=i):
                result = self.repo.check_log(int_mid_a, i)
                self.assertTrue(result)

        for i in data_b:
            with self.subTest(intv_mid=int_mid_b, item=i):
                result = self.repo.check_log(int_mid_b, i)
                self.assertTrue(result)

        self.repo.set_config(self.repo_kwargs)
        while self.repo.pending_repo_config_datetime() is not None:
            pass

    def test_hash_found_interval_start(self):
        """
        Log: check existing hash specifying start-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']
        n = muteacle.interval_number(dt, time_res_s)
        intv_start = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n
        )

        for i in data:
            with self.subTest(intv_start=intv_start, item=i):
                result = self.repo.check_log(intv_start, i)
                self.assertTrue(result)

    def test_hash_not_found_interval_mid(self):
        """
        Log: check non-existing hash specifying middle-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_start = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n
        )
        intv_mid = intv_start + timedelta(seconds=time_res_s/2)

        result = self.repo.check_log(intv_mid, self.item_skipped)
        self.assertFalse(result)

    def test_hash_not_found_interval_mid_class_change(self):
        """
        Log: check non-existing hash using mid-interval datetime
        across changes in hasher configuration.

        """
        time_res_s = self.repo._config['time_res_s']
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_class=self.repo.supported_hashers['ScryptHasher'],
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']

        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_class=self.repo.supported_hashers['PBKDF2Hasher'],
            hasher_config=self.hasher_kwargs
        )

        n = muteacle.interval_number(dt_a, time_res_s)
        intv_mid = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s, n
        )

        result = self.repo.check_log(intv_mid, self.item_skipped)
        self.assertFalse(result)

    def test_hash_not_found_interval_mid_trs_downgrade(self):
        """
        Log: check non-existing hash /w mid-interval datetime /w trs downgrade
        Repository must confirm the absence of a hash regardless of
        changes in the time_res_s setting. This test verifies test
        negatives across downgrades of time_res_s (larger time_res_s
        means a coarser time resolution).

        """
        time_res_s_a = 1
        self.repo.set_config({'time_res_s': time_res_s_a})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']
        n_a = muteacle.interval_number(dt_a, time_res_s_a)
        int_mid_a = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_a, n_a
        )

        time_res_s_b = 2
        self.repo.set_config({'time_res_s': time_res_s_b})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_b = req_b['datetime']
        n_b = muteacle.interval_number(dt_b, time_res_s_b)
        int_mid_b = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_b, n_b
        )

        result_a = self.repo.check_log(int_mid_a, self.item_skipped)
        self.assertFalse(result_a)
        result_b = self.repo.check_log(int_mid_b, self.item_skipped)
        self.assertFalse(result_b)

    def test_hash_not_found_interval_mid_trs_upgrade(self):
        """
        Log: check non-existing hash /w mid-interval datetime /w trs upgrade
        Repository must confirm the absence of a hash regardless of
        changes in the time_res_s setting. This test verifies test
        negatives across upgrades of time_res_s (smaller time_res_s
        means a finer time resolution).

        """
        time_res_s_a = 2
        self.repo.set_config({'time_res_s': time_res_s_a})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_a = self.get_logging_test_data()
        req_a = self.repo.append_log(
            data_a,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_a = req_a['datetime']
        n_a = muteacle.interval_number(dt_a, time_res_s_a)
        int_mid_a = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_a, n_a
        )

        time_res_s_b = 1
        self.repo.set_config({'time_res_s': time_res_s_b})
        while self.repo.pending_repo_config_datetime() is not None:
            pass
        data_b = self.get_logging_test_data()
        req_b = self.repo.append_log(
            data_b,
            hasher_config=self.hasher_kwargs_sc
        )
        dt_b = req_b['datetime']
        n_b = muteacle.interval_number(dt_b, time_res_s_b)
        int_mid_b = muteacle.interval_mid(
            dt_a.year, dt_a.month, dt_a.day, time_res_s_b, n_b
        )

        result_a = self.repo.check_log(int_mid_a, self.item_skipped)
        self.assertFalse(result_a)
        result_b = self.repo.check_log(int_mid_b, self.item_skipped)
        self.assertFalse(result_b)


    def test_hash_not_found_interval_start(self):
        """
        Log: check non-existing hash specifying start-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_start = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n
        )

        result = self.repo.check_log(intv_start, self.item_skipped)
        self.assertFalse(result)

    def test_hash_not_found_interval_end(self):
        """
        Log: check non-existing hash specifying end-of-interval datetime

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_end = muteacle.interval_end(
            dt.year, dt.month, dt.day, time_res_s, n
        )

        result = self.repo.check_log(intv_end, self.item_skipped)
        self.assertFalse(result)

    def test_hash_not_found_before_interval(self):
        """
        Log: check existing hash specifying datetime before interval
        The Repository must fail to verify existence of a hash if a
        datetime of the incorrect interval is specified.

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_early = muteacle.interval_end(
            dt.year, dt.month, dt.day, time_res_s, n-1
        )

        # logged data
        for i in data:
            with self.subTest(intv_early=intv_early, item=i):
                result = self.repo.check_log(intv_early, i)
                self.assertFalse(result)
        # unlogged data
        self.assertFalse(self.repo.check_log(intv_early, self.item_skipped))

    def test_hash_not_found_block_after_end(self):
        """
        Log: check existing hash specifying datetime after interval
        The Repository must fail to verify existence of a hash if a
        datetime of the incorrect interval is specified.

        """
        time_res_s = self.repo._config['time_res_s']
        data = self.get_logging_test_data()
        req = self.repo.append_log(
            data,
            hasher_class=self.hasher_class,
            hasher_config=self.hasher_kwargs
        )
        dt = req['datetime']

        n = muteacle.interval_number(dt, time_res_s)
        intv_late = muteacle.interval_start(
            dt.year, dt.month, dt.day, time_res_s, n+1
        )

        # logged data
        for i in self.data:
            with self.subTest(intv_late=intv_late, item=i):
                result = self.repo.check_log(intv_late, i)
                self.assertFalse(result)
        # unlogged data
        self.assertFalse(self.repo.check_log(intv_late, self.item_skipped))

