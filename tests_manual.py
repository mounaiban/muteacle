"""
Muteacle Manual Testing Environment

Objects for use in manual testing in a Python REPL environment

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

import pdb
import muteacle
from datetime import datetime, timedelta
from secrets import token_bytes

# Examples
repo_sqlite = muteacle.SQLiteRepository(db_keep_open=True)
salt_length = 32
items_a = (b'A1', b'A2', b'A3')
items_b = (b'B1', b'B2', b'B3')
hasher_s1 = muteacle.ScryptHasher(token_bytes(salt_length))
hasher_s2 = muteacle.ScryptHasher(token_bytes(salt_length), keylen=64)

def dump_sqlrepo_log_table(sqlrepo):
    if not isinstance(sqlrepo, muteacle.SQLiteRepository):
        raise TypeError('this helper is only for SQL repositories')
    scr = 'SELECT * FROM MuteacleLog'
    cur = sqlrepo.get_db_conn().execute(scr)
    rows = cur.fetchall()
    print('all log entries:', rows, sep='\n')
    return rows

def dump_sqlrepo_hasher_table(sqlrepo):
    if not isinstance(sqlrepo, muteacle.SQLiteRepository):
        raise TypeError('this helper is only for SQL repositories')
    scr = 'SELECT * FROM MuteacleHasherConfigs'
    cur = sqlrepo.get_db_conn().execute(scr)
    rows = cur.fetchall()
    print('all hashers:', rows, sep='\n')
    return rows

def dump_sqlrepo_config_table(sqlrepo):
    if not isinstance(sqlrepo, muteacle.SQLiteRepository):
        raise TypeError('this helper is only for SQL repositories')
    scr = 'SELECT * FROM MuteacleRepositoryConfigs'
    cur = sqlrepo.get_db_conn().execute(scr)
    rows = cur.fetchall()
    print('all repo configs:', rows, sep='\n')
    return rows

def test_append_log_scrypt(repository, items):
    salt = token_bytes(salt_length)
    hasher = muteacle.ScryptHasher(salt)
    repository.append_log(items, hasher)

