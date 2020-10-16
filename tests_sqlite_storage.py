"""
Muteacle SQLite Repository Test Suite (in storage)

This test suite repeats the tests in the module ``tests_sqlite``,
but with writing to the file system.

Running the test suite leaves files in the source tree with names
similar to ``_db_test_sqlite_2101-12-25_1.0-mk1.sqlite3``.  These
files may be safely deleted without affecting use of the library.

The filenames contain a run date (without time) and the target
library version number. A new file is created for every day one or
more tests are run. Incorrect timekeeping on the system running the
tests will result in inaccurate filenames.

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

import tests_sqlite as ts
# The following imports are repeated for readability purposes
import muteacle
from sqlite3 import OperationalError
from datetime import date, datetime, timedelta

dt_run = date.today()
ver = muteacle.ver_str
db_path = "_db_test_sqlite_{0}_{1}.sqlite3".format(ver, str(dt_run))
repo_test_onstorage_config_kwargs = {'db_path': db_path, 'time_res_s': 1}

class SetupTests(ts.SetupTests):
    """
    Repository Setup Tests to be executed using SQLite Repository
    instances in storage memory

    """
    repository_class = muteacle.SQLiteRepository
    repo_kwargs = repo_test_onstorage_config_kwargs

    def test_repo_multi_pending_configs(self):
        """
        Repository: multiple pending configs (SQLite, on storage)
        Databases with multiple pending repository configurations
        must be opened read-only.

        Any attempt to create hashers, change the repository
        configuration or to witness new items must fail.

        Only one pending configuration is currently permitted.
        Encountering multiple pending repository configurations is
        currently regarded as an indication of an incorrectly-set
        system clock.

        """
        path_a = "_db_test_sqlite_{0}_{1}-mprc.sqlite3".format(ver, str(dt_run))
        repo_a = self.repository_class(db_path=path_a)
        config_json = repo_a.json() # closes database connection
        # write multiple future configurations
        repo_a._read_only = False
        conn_a = repo_a.get_db_conn(mode='rw')
        sc = """
             INSERT INTO MuteacleRepositoryConfigs(
                timestamp, config, configHash
             ) VALUES (?, ?, ?)
             """
        for i in range(1, 3):
            dt_future = datetime.utcnow() + timedelta(days=i)
            ts_future = dt_future.timestamp()
            conn_a.execute(sc, (ts_future, config_json, ''))
        conn_a.commit()
        repo_a.close_db()

        # attempt to access database file with another repository
        repo_b = self.repository_class(db_path=path_a)

        self.assertTrue(repo_b._read_only)
        with self.assertRaises(OperationalError):
            meta = {'test': 'repo_multi_pending_configs'}
            repo_b.set_config({'meta': meta})
        with self.assertRaises(OperationalError):
            repo_b.new_hasher()
        with self.assertRaises(OperationalError):
            data = (b'alfa', b'bravo')
            repo_b.append_log(data)

# NOTE: Test hasher security has been downgraded to speed up testing
class LoggingTests(ts.LoggingTests):
    """
    Repository Log Witnessing Tests to be executed using SQLite
    Repository instances in storage memory

    """
    hasher_class = muteacle.PBKDF2Hasher
    hasher_kwargs = {'hash_algorithm': 'sha1', 'i': 500, 'keylen': 16,}
    repository_class = muteacle.SQLiteRepository
    repo_kwargs = repo_test_onstorage_config_kwargs

