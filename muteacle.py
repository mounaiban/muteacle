"""
Muteacle Shadow Logging System Main Module

Muteacle is a library implementing a shadow logging system which
'witnesses', or recognises data items without storing any details
of the witnessed data. Shadow logs store only enough information to
verify witnessing, but not enough to reconstruct the original data.

This library was originally created to help investigate the
plausibility of confidentiality-preserving, long-term data retention
systems.

Similar systems are already in wide use, at time of writing, to
securely store passwords. Muteacle extends this secure data
recognition ability to arbitrary data types, and combines it with a
time-based verification system.

Users (which may be applications or human operators) are to present
data to the shadow log, while remembering the time of witnessing.
To verify that the system has witnessed the data, the user presents
the exact data for a second time, with the approximate time (whose
required precision is user-configurable) of the original witnessing.
If the system confirms the witnessing, it responds with a boolean
True, or a False otherwise.

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

import hashlib
import sqlite3
import json
from base64 import b64encode, b64decode
from datetime import datetime, timedelta
from secrets import token_bytes
from time import sleep

# Attributes and Objects
ver_str = '0.1.1-mk9'
json_encoder = json.JSONEncoder()
json_decoder = json.JSONDecoder()

# Helper Functions

def dict_to_qstring(d, keys=None):
    """
    Convert a ``dict``, ``d`` to a comma-separated "key=value"
    string. To process only select keys, specify an ``iter`` of key
    names as ``keys``. This function currently only processes
    ``str`` keys and values.

    Non-string keys or values are ignored.

    Returns an ``str`` representation of ``d``.

    """
    if keys is None:
        ks = d.keys()
    else:
        ks = keys

    out = ''
    for k in ks:
        if isinstance(k, str) is False:
            continue
        try:
            val = d[k]
            if (isinstance(val,str) is False):
                val = str(val)
        except KeyError:
            continue
        append = "{0}={1},".format(k, val)
        out = "".join((out, append))

    return out[:-1] # Return string dropping terminal comma

def dict_to_json(d, keys=None, json_encoder=json_encoder):
    # Partially convert a dict to a JSON string, selecting values
    # of keys in ``keys`` only.
    # Returns JSON string.
    # This helper is currently exclusively used tests.
    if keys is None:
        ks = d.keys()
    else:
        ks = keys

    d_tmp = {}
    for k in ks:
        try:
            d_tmp[k] = d[k]
        except KeyError:
            continue
    return json_encoder.encode(d_tmp)

def interval_next_common_start(dt, time_res_s_a, time_res_s_b):
    # Find the datetime of the next earliest co-incident interval
    # start of two time_res_s values, or the closest future datetime
    # that is both an interval start for intervals of both length
    # time_res_s_a and time_res_s_b.
    # Returns datetime.
    tr_coarse = max(time_res_s_a, time_res_s_b)
    tr_fine = min(time_res_s_a, time_res_s_b)
    n_coarse = interval_number(dt, tr_coarse)
    td = timedelta(days=1)
    dt_tomorrow = datetime(year=dt.year, month=dt.month, day=dt.day) + td
    while dt < dt_tomorrow:
        n_coarse += 1
        isc = interval_start(dt.year, dt.month, dt.day, tr_coarse, n_coarse)
        n_fine = interval_number(isc, tr_fine)
        isf = interval_start(isc.year, isc.month, isc.day, tr_fine, n_fine)
        if isc == isf:
            return isf
        dt = isc
    return dt_tomorrow

def interval_number(dt, time_res_s):
    """
    Find the day interval number exactly at datetime dt, given the
    time resolution as an ``int`` in seconds ``time_res_s``.

    Returns the interval number as in ``int``.
    """
    # TODO: Constrain time_res_s to valid values and reject non-datetime
    # values for dt
    seconds = 3600*dt.hour + 60*dt.minute + dt.second
    return seconds // time_res_s

def interval_mid(year, month, day, time_res_s, n):
    # Find datetime at exact middle of interval
    # TODO: Constrain time_res_s to valid values
    start = interval_start(year, month, day, time_res_s, n)
    return start + timedelta(seconds=time_res_s/2)

def interval_start(year, month, day, time_res_s, n):
    # Find datetime at interval start
    last_mn = datetime(year=year, month=month, day=day) # last midnight
    return last_mn + timedelta(seconds=time_res_s*n)

def interval_end(year, month, day, time_res_s, n):
    # Find datetime at interval end
    last_mn = datetime(year=year, month=month, day=day)
    return last_mn + timedelta(seconds=time_res_s*(n+1), microseconds=-1)

def interval_seconds_left(dt, time_res_s):
    """
    Find the number of seconds left on the day interval at the
    moment of datetime ``dt``, given the time resolution ``time_res_s``.

    Returns number of seconds left in interval as ``float``.

    """
    intv_next = interval_number(dt, time_res_s) + 1
    midnight = datetime(year=dt.year, month=dt.month, day=dt.day)
    dt_intv_next = midnight + timedelta(seconds=intv_next*time_res_s)
    tleft = dt_intv_next - dt
    return tleft.total_seconds()

def join_dict(dict_a, dict_b):
    """
    Concatenates ``dict``'s ``dict_a`` and ``dict_b``.

    Returns a single ``dict`` which is a concatenation of the two
    ``dict``'s.

    Output Format
    -------------
    Two ``dict``'s with different keys and values will be simply
    combined:

    {'a':1, 'b':2} + {'c':3, 'd':4}) = {'a':1, 'b':2, 'c':3, 'd':4}

    Two ``dict``'s with different keys but identical values will
    also be simply combined:

    {'a':0, 'b':0} + {'c':0, 'd':0} = {'a':0, 'b':0, 'c':0, 'd':0}

    When joining ``dict``'s with matching keys but different values,
    the values will be packed into tuples:

    {'a':1, 'b':2} + {'a':10, 'b':20} = {'a':(1, 10), 'b':(2, 20)}

    Existing collections will be joined as well. The order of the
    items in the original collections (or sequences) will be preserved,
    with the collection in ``dict_b`` tacked on the end of the
    collection in ``dict_a``:

    {'a':(1, 100)} + {'a':(11, 1100)} = {'a':(1, 100, 11, 1100)}

    Notes
    -----
    This function can be slow if used frequently due to the amount
    of memory accesses involved. Please minimise its use.

    """
    msg_dict_only = 'only dicts are supported'
    if isinstance(dict_a, dict) is not True:
        raise TypeError(msg_dict_only)
    elif isinstance(dict_b, dict) is not True:
        raise TypeError(msg_dict_only)

    out = {}

    for k in dict_a.keys():
        out[k] = dict_a[k]

    for k in dict_b.keys():
        tmp_a = out.get(k)
        tmp_b = dict_b.get(k)
        if tmp_a is None:
            # key exists in dict_b only
            out[k] = dict_b[k]
        elif tmp_a != tmp_b:
            # key exists in both dicts, but values are different
            aval_coll = hasattr(tmp_a,'__iter__') and not isinstance(tmp_a,str)
            bval_coll = hasattr(tmp_b,'__iter__') and not isinstance(tmp_b,str)
            if aval_coll and bval_coll:
                # handle non-str iters (tuples, lists) appropriately
                out[k] = tmp_a + tmp_b
            elif aval_coll:
                out[k] = tmp_a + (tmp_b,)
            elif bval_coll:
                out[k] = (tmp_a,) + tmp_b
            else:
                # str's are handled by this case
                # strings are iter's but require special treatment
                out[k] = (tmp_a, tmp_b)
    return out

def sleep_until_interval_end(time_res_s):
    dt = datetime.utcnow()
    n = interval_number(dt, time_res_s)
    dt_inend = interval_end(dt.year, dt.month, dt.day, time_res_s, n)
    td = dt_inend - dt
    sleep(td.total_seconds())

# Reference Template Classes

class MuteacleConfigurable:
    """
    Base class to support the configuration system.

    Classes that have any degree of configurability inherit from
    this class.

    Format
    ------
    All ``MuteacleConfigrable``'s have two important constants
    to support their configurability:

    * ``set_config_keys`` - a ``tuple`` of ``str``'s defining
      supported configuration keywords.

    * ``defaults`` - a ``dict`` containing values defining the
      defaults for each configuration item.

    """
    set_config_keys = ('meta',)
    defaults = { 'meta' : {} }


    def __init__(self, **kwargs):
        """
        To initialise a Configurable:

        ::
            obj(key_a=value_a, key_b=value_b, ...)

        Where key_a, key_b, ... are keywords in ``set_config_keys``.

        The following configurables are to be supported by all
        subclasses:

        * meta - ``dict`` containing miscellaneous values (metadata)
          which are not used by Muteacle, but would be useful
          to the user.

        See set_config() on how the configuration mechanism works.

        """
        self._config = {}
        if kwargs.get('set_config', True) is not False:
            self.set_config(kwargs)

    @classmethod
    def fromJSON(self, json_str, decoder=json.JSONDecoder()):
        # Create configurable object from JSON string
        out = self()
        cfg = {}
        tmp = decoder.decode(json_str)
        for k in out.set_config_keys: # TODO: why do this so?
            cfg[k] = tmp.get(k, out.defaults[k])
        out.set_config(cfg)
        return out

    def get_config(self):
        """
        Returns the configuration of the object as a ``dict``
        """
        out = {}
        for k in self._config.keys():
            out[k] = self._config[k]
        return out

    def json(self, encoder=json.JSONEncoder()):
        # Output JSON string representation of current configuration
        return encoder.encode(self.get_config())

    def set_config(self, config={}):
        """
        Sets the configuration values on the object, according to
        the values in the ``dict``-like object ``config``.

        Returns an ``int`` indicating the number of changes made
        to the object's configuration.

        Configuration Mechanism
        -----------------------
        For every item in a ``dict``-like with a recognised key,
        the item is copied into the object's config ``dict``.
        On the first call, this method substitutes missing values
        with values from ``defaults``. On repeat calls, missing
        recognised values are interpreted as a no-change.

        If ``config`` is set to None, default values are applied
        on all recognised values, including ``meta``.

        An example object ``obj`` is of a class whose recognised
        keys as defined in ``set_config_keys`` are:
        ``('flavour', 'size')``

        Default values as defined in ``defaults`` are:
        ``{'flavour':'vanilla', 'size':'small', 'meta':{}}``

        The result of attempts to set the object configuration is
        defined as follows:

        Config 1:

        ::
            cfg = {'flavour':'mocha', 'size':'x-large'}``
            obj.set_config(config=cfg)``

        Result 1:

        ``self._config = {'flavour':'mocha', 'size':'x-large', 'meta':{}}``

        Config 2:

        ::
            cfg = {'flavour':'mocha', 'size':'x-large', 'vegan':True}

        Result 2:

        ``self._config = {'flavour':'mocha', 'size':'x-large', 'meta':{}}``
        No changes are made as unrecognised values are ignored.

        Config 3:

        ::
            cfg = {'halal':True, 'kosher':True}

        Result 3:

        ``self._config = {'flavour':'vanilla', 'size':'small', 'meta':{}}``
        No changes are made as unrecognised values are ignored.

        Config 4:

        ::
            cfg = {'flavour':'mocha'}

        Result 4:

        ``self._config = {'flavour':'mocha', 'size':'small', 'meta':{}}``

        Config 5:

        ::

            cfg = {'size':'small', 'size':'medium', 'size':'tiny'}

        Result 5:

        ``self._config = {'flavour':'vanilla', 'size':'tiny', 'meta':{}}``
        Recall that (as of Python 3.8), declaring a value of the
        same key multiple times in a ``dict`` results in only the
        last value taking effect.

        The method always returns the number of keys in ``set_config_keys``
        (``3`` in this example) on the first call.

        The configuration mechanism was designed for easy exporting
        and importing of configuration values between objects and
        databases.

        Notes
        -----
        Contrast the usage of this method to the constructor
        ``__init__()``. This method accepts configuration values only
        in a single ``dict``, while ``__init__()`` accepts values
        only in separate keyword arguments.

        """
        changes = 0

        if config is None:
            # Reset to defaults
            for k in self.set_config_keys:
                self._config[k] = self.defaults[k]
                changes += 1

        elif len(self._config.keys()) <= 0:
            # First configuration
            for k in self.set_config_keys:
                self._config[k] = config.get(k, self.defaults[k])
                changes += 1

        else:
            # Reconfiguration
            for k in self.set_config_keys:
                val = config.get(k)
                val_self = self._config[k]
                if val is not None:
                    if val != val_self:
                        self._config[k] = config[k]
                        changes += 1

        return changes

class Hasher(MuteacleConfigurable):
    """
    Hash generator object base class

    This base class is a prototype to guide the design of Hashers
    for use with Muteacle. To implement a new Hasher, override:

    * ``get_hash()`` with a hash derivation method,

    * ``set_config_keys`` with keys representing configurable values

    * ``defaults`` with default values for each configurable value.

    Please check the documentation on ready-to-use Hashers for
    usage instructions, as the exact mode of operation may vary
    sigificantly, especially for configuration.

    """
    set_config_keys = ()
    defaults = {}

    def __init__(self, salt, **kwargs):
        """
        Constructor method. All implementations must accept ``salt``
        as a ``bytes``-like object.

        Changes are generally not required. Please document the
        ``kwargs`` accepted by the Hasher class.

        PROTIP: Docstrings are inherited (i.e. copy-pasted) from the
        base class for undocumented members of the subclass. Take
        advantage of this to minimise documenting effort and maximise
        accuracy...

        """
        self.set_config_keys += super().set_config_keys
        self.defaults = join_dict(self.defaults, super().defaults)
        self.salt = salt

        super().__init__(**kwargs)

    @classmethod
    def fromJSON(self, json_str, decoder=json.JSONDecoder(), **kwargs):
        # Supported kwargs: salt
        salt = kwargs.get('salt', token_bytes(32))

        cfg = {}
        tmp = decoder.decode(json_str)
        self.set_config_keys += super().set_config_keys
        self.defaults = join_dict(self.defaults, super().defaults)
        for k in self.set_config_keys:
            cfg[k] = tmp.get(k, self.defaults[k])
        return self(salt, **cfg)

    def __eq__(self, other):
        """
        Method to support equality checks (i.e. a == b) with Hashers.

        Two Hashers are considered equal if *all* of the following
        are True:

        * Both Hashers are of the same class.

        * Their configuration and metadata are identical in terms
          of recognised keywords and set values.

        * Their salts are identical.

        """
        if isinstance(other, Hasher) is False:
            raise TypeError('cannot compare with non-hasher')

        if self.__class__.__name__ != other.__class__.__name__:
            # subclass must be the same
            return False

        if self.salt != other.salt:
            # salts must be identical
            return False

        # recognised keywords must be identical
        ks = self._config.keys()
        ks_other = other._config.keys()
        if ks != ks_other:
            return False

        for k in ks:
            # set config must be identical
            if self._config[k] != other._config[k]:
                return False

        return True

    def __repr__(self):
        """
        As a Python expert, you should know what this is...

        """
        f = '{0}({1})'
        cfg = self.get_config()
        cfg['salt'] = self.salt
        cfg_str = dict_to_qstring(cfg)
        out = f.format(self.__class__.__name__, cfg_str)
        return out

    def get_hash(self, data):
        """
        Returns the computed hash of ``data``, as a ``bytes``-like
        object.

        Argument ``data`` is a ``bytes``-like object.

        """
        # Please override me
        raise NotImplementedError

class Repository(MuteacleConfigurable):
    """
    Hash Log (Shadow Log) Repository Base Class

    Repositories serve as an interface between Muteacle and a
    persistent storage backend which holds the Hash Log and
    configuration information.

    """
    # When creating a Repository object to access a log in storage,
    # most kwargs only take effect during the creation of the
    # database. Subsequent accesses will apply the last saved
    # configuration, ignoring these kwargs.

    defaults = {
        'time_res_s' : 5,
        'salt_length' : 32,
        'hasher_class_name' : 'ScryptHasher',
    }
    set_config_keys = ('time_res_s', 'salt_length')
    supported_hashers = {} # See __init__() for actual list

    def __init__(self, **kwargs):
        """
        Please check the documentation of ready-to-use classes
        for setup details.

        """
        # Attributes
        self.supported_hashers = {
            'PBKDF2Hasher' : PBKDF2Hasher,
            'ScryptHasher' : ScryptHasher,
        }
        self.defaults = join_dict(self.defaults, super().defaults)
        self.set_config_keys += super().set_config_keys
        self._read_only = False

        super().__init__(**kwargs)

    def append_log(self, items, **kwargs):
        """
        Add all items in ``items`` to the Hash Log.

        ``items`` is a tuple or any other sequence containing
        ``bytes``-like objects.

        Returns a report in the form of a tuple like
        ``(s, c, dt)``, where:

        * ``s`` is the number of successful insertions

        * ``c`` is the total item count in ``items``

        * ``dt`` is the authoritative datetime to be used when
          checking the logs for hashes of **all items** in ``items``
          with ``check_log()``.

        A custom Hasher may be specified in ``hasher``. When
        ``hasher`` is None, the Repository automatically loads
        or creates an appropriate Hasher. Note that the user
        assumes responsibility for maintaining a means of recalling
        the hash from the Log when custom Hashers are used.

        """
        raise NotImplementedError

    def check_config(self):
        """
        Verify the configuration of the Repository for correctness.

        Returns ``None`` if no errors are found, or an error report
        as a ``dict`` if if any are discovered.

        Error Report Format
        -------------------
        An Error Report is a ``dict`` with problematic configuration
        keys as its keys, and brief error messages or error numbers
        as values. The names of keys used in the report must match
        its corresponding key in ``set_config_keys``.

        """
        # TODO: Re-implement this method under MuteacleConfigurable
        # using a more modular design.
        errors = {}

        # time_res_s must be an int larger than 0
        time_res_s = self._config['time_res_s']
        if time_res_s <= 0:
            errors['time_res_s'] = 'time_res_s <= 0'

        # time_res_s must divide 86400 into a whole number
        elif (86400%time_res_s != 0):
            errors['time_res_s'] = '86400%time_res_s != 0'

        if len(errors.keys()) <= 0:
            return None
        else:
            return errors

    def check_log(self, dt, item):
        """
        Find out if the Hash Log has been witnessed a particular data
        item at a sufficiently approximate date and time.

        Returns ``True`` if ``data`` is recognised, ``False`` otherwise.

        Arguments:

        * ``item``: ``bytes``-like object representing the data item to
          be checked,

        * ``dt``: ``datetime`` object referring to the approximate time
          when ``item`` was supposed to have been witnessed. The accuracy
          required is determined by ``time_res_s`` at witnessing time.

        """
        # TODO: Explain the interval system, and how time accuracy works
        # in Muteacle

        # Please override me
        raise NotImplementedError

    def close_db(self):
        """Closes the handle or connection to the database."""
        # NOTE: Some db systems may not require or actually use an
        # explicit closing function call. If using such a system,
        # simply override with a dummy method.
        raise NotImplementedError

    def get_config(self):
        """
        Returns the active configuration for the Repository.

        This method is overriden from MuteacleConfigurable to ensure
        that the Repository configuration is consistent with the
        knowledge of the underlying database.

        """
        raise NotImplementedError

    def get_hashers(self, dt):
        """
        Returns a ``tuple`` of Hashers required to rebuild Hashes
        logged at around the same day interval of ``datetime`` ``dt``.

        """
        raise NotImplementedError

    def load_repo_configs(self, dt=None):
        """
        Returns the Repository configurations at or the next earliest
        Python ``datetime``, ``dt``

        If ``dt`` is ``None``, the latest configuration is loaded
        instead.

        Note that this method only retrieves configuration information,
        please use ``set_config()`` to apply it. For compatibility reasons,
        more than one configuration is allowed to have the same datetime.

        """
        raise NotImplementedError

    def new_hasher(self, hasher_class=None, config={}):
        # Returns a dict with values: hasher, datetime
        raise NotImplementedError

    def pending_repo_config(self):
        raise NotImplementedError

    def pending_repo_config_datetime(self):
        raise NotImplementedError

    def save_hasher_config(self, hasher):
        """
        Save information required to rebuild the Hasher ``hasher``
        into the database.

        Returns the earliest datetime by which a hasher may be recalled.

        Hashers are recalled using ``get_hashers()``.

        Raises ``TypeErrors`` if an attempt is made to save a Hasher
        that is unsupported by the Repository.

        """
        raise NotImplementedError

# Built-in Ready-to-use Classes

class ScryptHasher(Hasher):
    """Hasher object supporting the Scrypt hashing algorithm"""
    set_config_keys = ('n', 'r', 'p', 'keylen')
    defaults = {
        'n' : 2**10,
        'r' : 16,
        'p' : 64,
        'keylen' : 32,
    }

    def __init__(self, salt, **kwargs):
        """
        The following arguments are supported:

        * ``n``

        * ``r``

        * ``p``

        * ``keylen``

        """
        super().__init__(salt, **kwargs)
        self.set_config(kwargs)

    def get_hash(self, data):
        n = self._config['n']
        r = self._config['r']
        p = self._config['p']
        keylen = self._config['keylen']
        return hashlib.scrypt(data, salt=self.salt, n=n, r=r, p=p)


class PBKDF2Hasher(Hasher):
    """
    Hasher object supporting the PBKDF2 hashing algorithm

    """
    set_config_keys = ('hash_algorithm', 'i', 'keylen')
    defaults = {
        'hash_algorithm' : 'sha256',
        'i' : 400000,
        'keylen' : 32,
    }

    def __init__(self, salt, **kwargs):
        """
        The following arguments are supported:

        * ``hash_algorithm``

        * ``i``

        * ``keylen``

        """
        super().__init__(salt, **kwargs)
        self.set_config(kwargs)

    def get_hash(self, data):
        al_name = self._config['hash_algorithm']
        i = self._config['i']
        keylen = self._config['keylen']
        return hashlib.pbkdf2_hmac(al_name, data, self.salt, i, keylen)


class SQLiteRepository(Repository):
    """
    Repository class for using Muteacle with SQLite Database Files

    """
    default_filename = 'muteacle-test.sqlite3'
    defaults = {
        'db_keep_open' : False,
        'db_path' : ':memory:',
    }
    table_spec = {
        'MuteacleHasherTypes' : (
            ('name', 'TEXT'),
        ),
        'MuteacleHasherConfigs' : (
            ('timestamp','REAL'),
            ('hasherTypeId', 'INT'),
            ('config', 'TEXT'),
            ('configHash', 'TEXT'),
            ('salt', 'TEXT'),
        ),
        'MuteacleRepositoryConfigs' : (
            ('timestamp', 'REAL'),
            ('config', 'TEXT'),
            ('configHash', 'TEXT'),
        ),
        'MuteacleLog' : (
            ('hash', 'TEXT'),
        ),
    }

    def __init__(self, **kwargs):
        """
        The following arguments are supported:

        * ``db_path`` - ``path``-like object specifying filesystem
          path to the SQLite database file. The default path is
          ``:memory:``, which creates an in-memory database.

        * ``db_keep_open`` - Set to ``True`` in order to keep the
          connection to the database file open, particularly when
          testing or when using certain database server setups.
          If ``db_path`` is set to ``:memory:``, this argument will 
          be set to ``True``.

        """
        # TODO: Prevent database writes if more than one future config
        # detected.
        self.defaults = join_dict(self.defaults, super().defaults)
        self._db_conn = None
        self._db_path = kwargs.get('db_path', self.defaults['db_path'])
        chtab = self._slr_check_db_tables()
        self._table_check_passed = (
            chtab['tables_expected'] == chtab['tables_verified']
        )
        if self._db_path == self.defaults['db_path']:
                self._db_keep_open = True
        else:
            self._db_keep_open = kwargs.get(
                'db_keep_open', self.defaults['db_keep_open']
            )

        self._slr_create_tables()
        super().__init__(**kwargs)
        self._slr_populate_supported_hashers_table()

        config_init = self.load_latest_repo_config()
        if config_init == {}:
            self.set_config(kwargs) # also saves the first config

    def append_log(self, items, **kwargs):
        # Submits an iter of data items for witnessing by the log
        # kwargs supported: hasher_class, hasher_config
        # May raise TypeError

        self._config = self.load_latest_repo_config()
        time_res_s = self._config['time_res_s']
        class_name = self.defaults['hasher_class_name']
        default_hasher_class = self.supported_hashers[class_name]
        hcls = kwargs.get('hasher_class', default_hasher_class)
        hcfg = kwargs.get('hasher_config', {})
        if hcls not in self.supported_hashers.values():
            raise TypeError('hasher of unsupported type requested')
        req_hasher = self.new_hasher(hasher_class=hcls, config=hcfg)
        hasher = req_hasher['hasher']

        report = self._slr_write_hashes(items, hasher)
        dt_hasher = req_hasher['datetime']
        return {
            'datetime': dt_hasher,
            'items_logged': report[0],
            'items': report[1],
        }

    def check_log(self, dt, item):
        out = False
        try:
            # set the repo config to match that when hash was committed
            configs = self.load_repo_configs(dt)
            # get all possible hashers, to generate all possible hashes
            hashers = self.get_hashers(dt)
            conn = self.get_db_conn(mode='ro')
            for h in hashers:
                # check every possible hash with the database
                mhash = h.get_hash(item)
                mhash_b64 = b64encode(mhash)
                mhash_str = str(mhash_b64)[2:-1]
                sc_check = "SELECT hash FROM MuteacleLog WHERE hash = ?"
                cus = conn.execute(sc_check, (mhash_str,))
                row = cus.fetchone()
                if row is not None:
                    # hash match!
                    out = True
        except ValueError:
            raise ValueError
        finally:
            if self._db_keep_open is not True:
                self.close_db()
        return out

    def close_db(self):
        if self._db_conn is not None:
            self._db_conn.close()
            self._db_conn = None

    def get_hashers(self, dt):
        out = []
        configs = self.load_repo_configs(dt)
        conn = self.get_db_conn(mode='ro')

        for c in configs:
            time_res_s = c['time_res_s']
            n = interval_number(dt, time_res_s)
            dt_n = interval_start(dt.year, dt.month, dt.day, time_res_s, n)
            ts_n = dt_n.timestamp()
            sc_get_hashers = """
                             SELECT * FROM MuteacleHasherConfigs
                             WHERE timestamp = ?
                             ORDER BY rowid DESC
                             """
            cus_config = conn.execute(sc_get_hashers, (ts_n,))
            cus_config.row_factory = sqlite3.Row
            rows_config = cus_config.fetchall()

            # generate hashers for each valid madatetime
            for row in rows_config:
                salt = b64decode(row['salt'])
                tid = row['hasherTypeId']
                sc_type_name = """
                               SELECT name from MuteacleHasherTypes
                               WHERE rowid = ?
                               """
                cus_type = conn.execute(sc_type_name, (tid,))
                cus_type.row_factory = sqlite3.Row
                row_tname = cus_type.fetchone()
                tname = row_tname['name']
                hclass = self.supported_hashers[tname]
                hasher_new = hclass.fromJSON(row['config'], salt=salt)
                out.append(hasher_new)

        if self._db_keep_open is not True:
            self.close_db()

        return out

    def load_repo_configs(self, dt=None):
        ts = None
        if dt is None:
            ts = datetime.utcnow().timestamp()
        else:
            ts = dt.timestamp()

        conn = self.get_db_conn(mode='ro')
        sc_ts = """
                SELECT timestamp
                FROM MuteacleRepositoryConfigs
                WHERE timestamp <= ?
                ORDER BY rowid DESC
                LIMIT 1
                """
        # NOTE: We cannot just use interval_start as timestamps
        # from Python ``datetime`` objects have more decimal places
        # than SQLite values
        cus = conn.execute(sc_ts, (ts,))
        cus.row_factory = sqlite3.Row
        row = cus.fetchone()

        if row is None:
            # no configs have been saved
            tts = ts
        else:
            tts = row['timestamp']

        sc_configs = """
                     SELECT * FROM MuteacleRepositoryConfigs
                     WHERE timestamp = ?
                     ORDER BY rowid DESC
                     """
        cus = conn.execute(sc_configs, (tts,))
        cus.row_factory = sqlite3.Row
        rows = cus.fetchall()

        if self._db_keep_open is not True:
            self.close_db()

        out = []
        jd = json.decoder.JSONDecoder()
        for r in rows:
            config_json = r['config']
            out.append(jd.decode(config_json))
        return out

    def new_hasher(self, hasher_class=None, config={}):
        # Request a new hasher.
        # Every change in hasher config produces a hasher of a
        # different salt.
        hasher_new = None
        dt = datetime.utcnow()
        hashers = self.get_hashers(dt)

        if len(hashers) > 0:
            # hashers found
            hasher_last = hashers[0]

            if hasher_class is None:
                # use the the class of the last saved
                # hasher if no hasher_class is specified
                hasher_class = hasher_last.__class__

            class_match = isinstance(hasher_last, hasher_class) is True

            if class_match:
                changes = hasher_last.set_config(config)
                if changes <= 0:
                    # effective config doesn't change
                    return {'hasher':hasher_last, 'datetime':dt}
                else:
                    # changes to hasher config requested
                    hasher_new = hasher_last
                    hasher_new.salt = token_bytes(self._config['salt_length'])

        else:
            # no hashers found
            if hasher_class is None:
                class_name = self.defaults['hasher_class_name']
                hasher_class = self.supported_hashers[class_name]

        salt = token_bytes(self._config['salt_length'])
        hasher_new = hasher_class(salt, **config)
        dt_n = self.save_hasher_config(hasher_new)
        return {'hasher':hasher_new, 'datetime':dt_n}

    def save_hasher_config(self, hasher):
        dt = datetime.utcnow()

        if isinstance(hasher, Hasher):
            repo_config = self.load_latest_repo_config()
            if repo_config == {}:
                # no repo config saved yet
                repo_config = self.get_config()
                self.set_config()
            time_res_s = repo_config['time_res_s']
            tid = self._slr_get_hasher_type_id(hasher)
            if tid is not None:
                config_json = hasher.json()
                salt_b64 = b64encode(hasher.salt)
                salt_str = str(salt_b64)[2:-1] # trim off python-specific stuff
                dt_n = self._slr_write_hasher_config(
                    time_res_s, tid, config_json, salt_str
                )
                return dt_n
            else:
                raise TypeError('hasher class unsupported')
        else:
            raise TypeError('unsupported or non-hasher')

    def pending_repo_config(self):
        req = self._slr_get_pending_repo_config()
        return req['config']

    def pending_repo_config_datetime(self):
        req = self._slr_get_pending_repo_config()
        return req['datetime']

    def get_config(self):
        # Uses _slr_get_active_repo_config()
        req = self._slr_get_active_repo_config()
        self._config = req['config']
        # in a Repository, self._config is a mini-cache
        return self._config

    def load_latest_repo_config(self):
        # Alternate method to get_config()
        # TODO: remove this method, and replace it with get_config()
        configs = self.load_repo_configs()
        if len(configs) > 0:
            self._config = configs[0]
            return configs[0]
        else:
            return {}

    def set_config(self, config=None):
        """
        Save information required to restore the Repository to the
        current configuration.

        May raise sqlite3.OperationalErrors in the event of technical
        difficulties when accessing the database files.

        """
        # TODO: Document exact behaviour of this method
        config_pend = {}

        if config is None:
            config = self.defaults

        req_active = self._slr_get_active_repo_config()
        config_active = req_active['config']

        if config_active == {}:
            # no previous config saved, save first repo config
            # immediately, backdated to start of current interval
            for k in self.set_config_keys:
                config_pend[k] = config.get(k, self.defaults[k])
            dt = datetime.utcnow()
            n_sched = interval_number(dt, config_pend['time_res_s'])
            dt_sched = interval_start(
                dt.year, dt.month, dt.day, config_pend['time_res_s'], n_sched
            )
            ts_sched = dt_sched.timestamp()
            config_json = json_encoder.encode(config_pend)
            self._slr_write_repo_config(ts_sched, config_json)
            return dt_sched

        else:
            for k in self.set_config_keys:
                config_pend[k] = config.get(k, config_active[k])
            req_sched = self._slr_get_pending_repo_config()
            config_sched = req_sched['config']
            if config_pend == config_sched:
                # requested config identical to pending config, do nothing
                return req_sched['datetime']
            elif config_pend == config_active:
                # requested config has no effective change
                self._slr_delete_pending_repo_configs()
                return req_active['datetime']
            else:
                # requested config is different
                dt = datetime.utcnow()
                trs_c = config_active['time_res_s']
                trs_n = config_pend['time_res_s']
                dt_sched = interval_next_common_start(dt, trs_c, trs_n)
                ts_sched = dt_sched.timestamp()
                config_pend_json = json_encoder.encode(config_pend)
                self._slr_delete_pending_repo_configs()
                self._slr_write_repo_config(ts_sched, config_pend_json)
                return dt_sched

    def get_db_conn(self, **kwargs):
        path = self._db_path
        if self._db_conn is None:
            if path is None:
                # NOTE: The :memory: database always opens in read-write.
                # This is currently tolerated, as :memory: is only used
                # for testing purposes.
                self._db_conn = sqlite3.connect(':memory:')
            else:
                uri = self._slr_get_db_uri(path, **kwargs)
                self._db_conn = sqlite3.connect(uri, uri=True)
            return self._db_conn
        else:
            return self._db_conn

    # SQLite Repository-specific methods

    def _slr_create_tables(self, **kwargs):
        """
        Creates tables in the database file specified in ``self._db_path``
        for use with Muteacle.

        Returns True if setup was successful or not required, False
        otherwise.

        May raise sqlite3.OperationalErrors in the event of technical
        difficulties when accessing the database files.

        Table Specification Format
        --------------------------
        Table specifications are stored in a ``dict`` like:

        ``{ 'table1':spec, 'table2':spec, ..., 'tableN': spec }``

        Where:

        * `'table1'` to `'tableN'` are the literal names of the tables
          to be used in the database file,

        * ``spec`` is a tuple of tuples like ``(cn, th)`` where:

            * ``cn`` is the literal name of the table column,

            * ``th`` is the Type Hint of the corresponding table column.
              Type Hints are explained in the SQLite Documentation.

        """
        if self._table_check_passed:
            return True

        else:
            try:
                # create tables
                conn = self.get_db_conn()
                conn.execute('BEGIN')
                for tname in self.table_spec:
                    csp_all = ""
                    for colspec in self.table_spec[tname]:
                        csp = "{} {}, ".format(colspec[0], colspec[1])
                        csp_all = "".join((csp_all, csp))
                    sc = 'CREATE TABLE {}({})'.format(tname, csp_all[:-2])
                    conn.execute(sc)
                conn.commit()
            except sqlite3.DatabaseError:
                return False
            finally:
                if self._db_keep_open is not True:
                    self.close_db()
            return True

    def _slr_populate_supported_hashers_table(self):
        """
        Write names of supported classes to the MuteacleHasherTypes
        table and assigned type ids. Returns None.

        May throw sqlite3.DatabaseError in the event of technical
        difficulties accessing the database file.

        This method is only intended to be run after the tables have
        been created in the database file with ``_slr_create_tables()``.

        """
        conn = self.get_db_conn()
        sc = "INSERT INTO MuteacleHasherTypes(name) VALUES (?)"
        for tname in self.supported_hashers.keys():
            conn.execute(sc, (tname,))
        conn.commit()
        # TODO: Find out how to use executemany(), if found to be
        # more beneficial than what's done here

        if self._db_keep_open is not True:
            self.close_db()

    def _slr_check_db_tables(self):
        """
        Check if tables with names and columns matching the Muteacle specs
        are in the nominated database file.

        Returns a ``dict`` of results with the following values:

        * tables_expected - Number of tables in specification

        * tables_found - Number of tables with names matching specification

        * tables_verified - Number of tables with names and columns
          matching specification

        NOTE: The check is skipped if the database path ``_db_path`` has
        been set to ``:memory:``. This happens when the Repository is run
        in volatile memory.

        May throw sqlite3.DatabaseError in the event of technical
        difficulties accessing the database file.

        """
        table_names = tuple(self.table_spec.keys())
        tables_expected = len(table_names)
        tables_found = 0
        tables_verified = 0
        results = {
            'tables_expected' : tables_expected,
            'tables_found' : tables_found,
            'tables_verified' : tables_verified,
        }

        if self._db_path == ':memory:':
            self._table_check_passed = False
            return results

        try:
            conn = self.get_db_conn(mode='ro')
            for tname in self.table_spec.keys():
                # FIXME: The DB-API qmark substitution doesn't work
                # for table names. Why?
                sc = 'SELECT * FROM {0}'.format(tname)
                curs = conn.execute(sc)
                # Get column names from table spec and check
                cnames = [cs[0] for cs in self.table_spec[tname]]
                tables_found += 1
                i = 0
                for d in curs.description:
                    if d[0] not in cnames:
                        break
                    else:
                        i += 1
                if i != len(cnames):
                    break
                else:
                    tables_verified += 1
        except sqlite3.OperationalError:
            pass
        finally:
            self.close_db()
            return results

    def _slr_get_db_uri(self, path, **kwargs):
        """
        Generates SQLite URIs for use with the sqlite3.connect()
        method.

        See Also:
        ---------
        * SQLite Documentation on Uniform Resource Identifiers:
          https://sqlite.org/uri.html

        """
        # TODO: document keywords
        keys_supported = ('mode', 'psow', 'immutable')
        q_opts = dict_to_qstring(kwargs, keys=keys_supported)
        if len(q_opts) > 0:
            return "file:{0}?{1}".format(path, q_opts)
        else:
            return "file:{0}".format(path)

    def _slr_write_hasher_config(self, time_res_s, type_id, config_json, salt_str):
        # Write Hasher to database.
        # Returns datetime of the earliest timestamp which is able to
        # recall the Hasher.
        conn = self.get_db_conn()
        sc = """
             INSERT INTO MuteacleHasherConfigs(
                timestamp,
                hasherTypeId,
                config,
                configHash,
                salt
             ) VALUES (?, ?, ?, ?, ?)
             """
        dt = datetime.utcnow()
        n = interval_number(dt, time_res_s)
        dt_n = interval_start(dt.year, dt.month, dt.day, time_res_s, n)
        ts_n = dt_n.timestamp()
        hhex = ''
        if (len(config_json) >= 128):
            config_bytes = bytes(config_json, 'utf-8')
            ho = hashlib.sha512(config_bytes)
            hhex = ho.hexdigest()
        conn.execute(sc, (ts_n, type_id, config_json, hhex, salt_str))
        conn.commit()
        if self._db_keep_open is not True:
            self.close_db()
        return dt_n

    def _slr_write_hashes(self, items, hasher):
        # Generates hashes of data items in ``items`` and saves them to
        # the database (witnessing). Returns a tuple as follows:
        # (items_logged, items_total)
        conn = self.get_db_conn()
        conn.execute('BEGIN')
        count = 0
        for i in items:
            if isinstance(i, bytes) is not True:
                continue
            mhsh = hasher.get_hash(i)
            mhsh_b64 = b64encode(mhsh)
            mhsh_str = str(mhsh_b64)[2:-1] # Trim off Python-specific stuff
            sc_append = "INSERT INTO MuteacleLog(hash) VALUES (?)"
            conn.execute(sc_append, (mhsh_str,))
            count += 1
        conn.commit()
        if self._db_keep_open is not True:
            self.close_db()
        return(count, len(items))

    def _slr_delete_pending_repo_configs(self):
        conn = self.get_db_conn()
        sc = "DELETE FROM MuteacleRepositoryConfigs WHERE timestamp > ?"
        ts_now = datetime.utcnow().timestamp()
        conn.execute(sc, (ts_now,))
        conn.commit()
        if self._db_keep_open is not True:
            self.close_db()

    def _slr_write_repo_config(self, timestamp, config_json):
        # Write Repository configuration to the database.
        # NOTE: Please do not use arbitrary timestamps that are not
        # exactly at an interval start without a good reason.
        conn = self.get_db_conn()
        sc = """
             INSERT INTO MuteacleRepositoryConfigs(
                timestamp, config, configHash
             ) VALUES (?, ?, ?)
             """
        hhex = ''
        if (len(config_json) >= 128):
            config_bytes = bytes(config_json, 'utf-8')
            ho = hashlib.sha512(config_bytes)
            hhex = ho.hexdigest()
        conn.execute(sc, (timestamp, config_json, hhex))
        conn.commit()
        if self._db_keep_open is not True:
            self.close_db()

    def _slr_get_active_repo_config(self):
        ts = datetime.utcnow().timestamp()
        conn = self.get_db_conn(mode='ro')
        sc = """
             SELECT * FROM MuteacleRepositoryConfigs
             WHERE timestamp <= ?
             ORDER BY rowid DESC
             """
        cus = conn.execute(sc, (ts,))
        cus.row_factory = sqlite3.Row
        row = cus.fetchone()
        if row is not None:
            config = json_decoder.decode(row['config'])
            dt = datetime.fromtimestamp(row['timestamp'])
        else:
            config = {}
            dt = None
        if self._db_keep_open is not True:
            self.close_db()
        return {'config': config, 'datetime': dt}

    def _slr_get_pending_repo_config(self):
        ts = datetime.utcnow().timestamp()
        conn = self.get_db_conn(mode='ro')
        sc = """
             SELECT * FROM MuteacleRepositoryConfigs
             WHERE timestamp > ?
             ORDER BY rowid ASC
             """
        cus = conn.execute(sc, (ts,))
        cus.row_factory = sqlite3.Row
        row = cus.fetchone()
        if row is not None:
            config = json_decoder.decode(row['config'])
            dt = datetime.fromtimestamp(row['timestamp'])
        else:
            config = {}
            dt = None
        if self._db_keep_open is not True:
            self.close_db()
        return {'config': config, 'datetime': dt}

    def _slr_get_hasher_type_id(self, hasher):
        conn = self.get_db_conn(mode='ro')
        sc = "SELECT rowid from MuteacleHasherTypes WHERE name = ?"
        class_name = hasher.__class__.__name__
        cus = conn.execute(sc, (class_name,))
        cus.row_factory = sqlite3.Row
        row = cus.fetchone()
        if self._db_keep_open is not True:
            self.close_db()
        if row is not None:
            return row['rowid']
        else:
            return None

    def _slr_get_pending_repo_configs_count(self, **kwargs):
        # Counts number of Repository configurations with future
        # timestamps. To be used for checking for scheduled changes,
        # or if time has been tampered with or misconfigured.
        conn = self.get_db_conn()
        sc = """
             SELECT count(*) FROM MuteacleRepositoryConfigs
             WHERE timestamp > ?
             """
        ts = datetime.utcnow().timestamp()
        cus = conn.execute(sc, (ts,))
        count = cus.fetchall[0][0]
        return min(count, 0)

