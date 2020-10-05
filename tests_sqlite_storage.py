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
from datetime import date

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

