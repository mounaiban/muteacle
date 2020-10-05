"""
Muteacle Generic Configurable Object Test Suite

This test suite verifies the functionality of the core methods
implemented on the Generic Configurable Object, MuteacleConfigurable.

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
from muteacle import MuteacleConfigurable, join_dict

class ConfigTester(MuteacleConfigurable):
    """ Class for an abstract fashion object for testing purposes"""
    set_config_keys = ('design', 'size',)
    defaults = {
        'design': 'plain_black',
        'size': 120
    }

    def __init__(self, **kwargs):
        self.defaults = join_dict(self.defaults, super().defaults)
        self.set_config_keys += super().set_config_keys
        super().__init__(**kwargs)

class TestMuteacleConfigurableSetConfig(unittest.TestCase):
    """Tests for MutacleConfigurable.set_config()"""

    def test_init_all_defaults(self):
        """Object creation with default configuration"""
        obj_test = ConfigTester()
        expected = {
            'meta' : {},
            'design' : 'plain_black',
            'size' : 120,
        }
        self.assertEqual(obj_test.get_config(), expected)

    def test_init_partial_config(self):
        """Object creation with partial customisation with kwargs"""
        obj_test = ConfigTester(size=160)
        expected = {
            'meta' : {},
            'design' : 'plain_black',
            'size' : 160,
        }
        self.assertEqual(obj_test.get_config(), expected)

    def test_init_from_json(self):
        """Object creation from JSON representation"""
        j = '{"meta":{"test":"init_from_json"}, "size":320}'
        obj_test = ConfigTester.fromJSON(j)
        expected = {
            'meta' : {'test': 'init_from_json'},
            'design' : 'plain_black',
            'size' : 320,
        }
        self.assertEqual(obj_test.get_config(), expected)

    def test_init_full_config(self):
        """Object creation with all possible config values changed"""
        obj_test = ConfigTester(
            meta={'country': 'it', 'material': 'nylon'},
            design='red_thorny_roses',
            size=110
        )
        expected = {
            'meta' : {'country': 'it', 'material': 'nylon'},
            'design' : 'red_thorny_roses',
            'size' : 110,
        }
        self.assertEqual(obj_test.get_config(), expected)

    def test_reconfig_partial_config(self):
        """Partial customisations during and after object creation"""
        obj_test = ConfigTester(meta={'country': 'it', 'sn': '00001'})
        obj_test.set_config( {'size':80} )
        expected = {
            'meta' : {'country': 'it', 'sn': '00001'},
            'design' : 'plain_black',
            'size' : 80,
        }
        self.assertEqual(obj_test.get_config(), expected)

