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
repo_test_config_kwargs = {'time_res_s': 1}
json_encoder = json.JSONEncoder()

# PROTIP: Keep time_res_s to a very short period during tests to allow
# quick testing of behaviours involving lapsing of intervals.

class SetupTests(mtr.SetupTests):
    """
    Repository Setup Tests to be executed using SQLite Repository
    instances.

    These tests are run in volatile memory.

    """
    repository_class = muteacle.SQLiteRepository
    repo_kwargs = repo_test_config_kwargs

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

