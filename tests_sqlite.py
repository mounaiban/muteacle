"""
Muteacle SQLite Repository Test Suite

This test suite verifies functionality and behaviour specific to
SQLite Repository support. This module repeats tests in the
``muteacle_tests_repository`` module with SQLiteRepository instances.

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

import muteacle_tests_repository as mtr
import muteacle
# The following imports are repeated for readability purposes
import json
import sqlite3
from datetime import datetime, date
from secrets import token_bytes

# Filename and test repository settings
repo_test_config_kwargs = {'db_keep_open': True, 'time_res_s': 1}
json_encoder = json.JSONEncoder()

# PROTIP: Keep time_res_s to a very short period during tests to allow
# quick testing of behaviours involving lapsing of intervals.

class SetupTests(mtr.SetupTests):
    """
    Repository Setup Tests to be executed using SQLite Repository
    instances.

    These tests are run in volatile memory.

    """
    # TODO: Replace these unit tests with tests SQLite Repository db
    # operation methods (_slr) in a future release. These tests can
    # generalised and moved to ``muteacle_tests_repository``.
    repository_class = muteacle.SQLiteRepository
    repo_kwargs = repo_test_config_kwargs

    def test_save_hasher_config(self):
        """
        Hasher: hasher configuration write test
        Repository must correctly write Hasher configuration to the
        database.

        """
        ts = datetime.utcnow().timestamp()
        meta = {'test': 'save_hasher_config', 'ts': ts}
        self.repo.set_config({'meta': meta})

        # create a new hasher from scratch and save it
        class_name = self.repo.defaults['hasher_class_name']
        hasher_class = self.repo.supported_hashers[class_name]
        salt = token_bytes(32)
        hasher = hasher_class(salt, meta=meta)
        self.repo.save_hasher_config(hasher)

        conn = self.repo.get_db_conn()
        config_json = hasher.json()
        sc = "SELECT rowid from MuteacleHasherConfigs WHERE config=?"
        cus = conn.execute(sc, (config_json,))
        rows = cus.fetchall()

        self.assertEqual(len(rows),1)

# NOTE: Test hasher security has been downgraded to speed up testing
class LoggingTests(mtr.RepositoryLoggingTests):
    """
    Repository Log Witnessing Tests to be executed using SQLite
    Repository instances in volatile memory.

    """
    hasher_class = muteacle.PBKDF2Hasher
    hasher_kwargs = {'hash_algorithm': 'sha1', 'i': 500, 'keylen': 16,}
    hasher_kwargs_sc = {'n': 2, 'r': 1, 'p': 2, 'keylen': 16,}
    repository_class = muteacle.SQLiteRepository
    repo_kwargs = repo_test_config_kwargs

