"""
Muteacle SQLite Hasher Equality Test Suite

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

# TODO: Generalise this test module, and repeat across all supported
# Hasher classes.

import muteacle
import unittest
from secrets import token_bytes

class HasherCoreTests(unittest.TestCase):

    def setUp(self):
        self.meta = {
            "app_specific_setting_a" : "alfa",
            "app_specific_setting_b" : "bravo",
        }

    def test_config_equals_default(self):
        """
        Hasher Equality: True when class and configuration are identical
        This test involves Hashers left in their default configuration
        """
        salt = token_bytes(32)
        hasher_a = muteacle.ScryptHasher(salt)
        hasher_b = muteacle.ScryptHasher(salt)
        self.assertEqual(hasher_a, hasher_b)

    def test_config_equals_custom(self):
        """
        Hasher Equality: True when class and configuration are identical
        This test involves Hashers set up to have identical configurations
        """
        salt = token_bytes(32)
        hasher_a = muteacle.ScryptHasher(salt, meta=self.meta, keylen=64)
        hasher_b = muteacle.ScryptHasher(salt, meta=self.meta, keylen=64)
        self.assertEqual(hasher_a, hasher_b)

    def test_config_not_equals_classes(self):
        """
        Hasher Equality: False when classes differ
        """
        salt = token_bytes(32)
        hasher_a = muteacle.PBKDF2Hasher(salt)
        hasher_b = muteacle.ScryptHasher(salt)
        self.assertNotEqual(hasher_a, hasher_b)

    def test_config_not_equals_salts(self):
        """
        Hasher Equality: False when salts differ
        """
        salt_a = token_bytes(32)
        salt_b = token_bytes(32)
        hasher_a = muteacle.ScryptHasher(salt_a)
        hasher_b = muteacle.ScryptHasher(salt_b)
        self.assertNotEqual(hasher_a, hasher_b)

    def test_config_not_equals_keys(self):
        """
        Hasher Equality: False when configurations have different keys
        """
        salt = token_bytes(32)
        hasher_a = muteacle.ScryptHasher(salt, meta=self.meta, keylen=64)
        hasher_b = muteacle.ScryptHasher(salt, keylen=64)
        self.assertNotEqual(hasher_a, hasher_b)

    def test_config_not_equals_values(self):
        """
        Hasher Equality: False when configs have same keys, different values
        """
        salt = token_bytes(32)
        hasher_a = muteacle.ScryptHasher(salt, meta=self.meta, keylen=32)
        hasher_b = muteacle.ScryptHasher(salt, meta=self.meta, keylen=64)
        self.assertNotEqual(hasher_a, hasher_b)

