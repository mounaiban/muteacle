Muteacle Shadow Logging System
------------------------------
*A Mounaiban Mini-Project*

What This?
==========
**Muteacle** is a *shadow logging system*, a database which
recognises data but doesn't recall any of it. There is only enough
information to verify if the data has been *witnessed* at a specific
time, but not enough to recover any details of the data.

Similar databases are in wide use for storing passwords; Muteacle
merely extends use of such databases to more data types and use cases.

By design, a sufficiently approximate time is enough to verify a
witnessing; there is no need for a split-second-precise datetime.
The required accuracy, or *time resolution* (internally known as
``time_res_s``) can be set by the user.

How Do I Use It?
================
1. Use the Repository classes to interact with the shadow log.
   At the moment ``SQLiteRepository`` is the only Repository available.

   ::

    >>> from muteacle import SQLiteRepository
    >>> import datetime
    >>> repo_test = SQLiteRepository(db_path='mutest.sqlite3')

   By default this creates a file mutest.sqlite3 in the source code
   directory.

2. Get the data ready, and witness it. Only byte arrays are accepted,
   so a type conversion is needed before witnessing. Multiple data items
   can be witnessed at once.


   ::

     >>> comments = ('amazing', 'interesting', 'lamentable', 'sacrilegious')
     >>> data = [bytes(d, 'utf-8') for d in comments]

   I hope you know your list comprehensions!
   
   Use the ``append_log()`` method to witness the data:

   ::

     >>> repo_test.append_log(data)
     {'datetime': datetime.datetime(2101, 12, 25, 2, 22, 10), ...}

   A report will be returned. The ``datetime`` is the most important,
   while ``items_logged`` and ``items`` indicate the number of items
   successfully witnessed versus the number of items submitted.

   **All Muteacle datetimes are in Universal Time Coordination (UTC).**

3. Verify the witnessing.

   Use ``check_log()`` to verify a witnessing. With the datetime in
   step 2, and the original data, query the shadow log:

   ::

    >>> dt = datetime.datetime(2101, 12, 25, 2, 22, 10)
    >>> c = bytes('interesting', 'utf-8')
    >>> repo_test.check_log(dt, c)
    True

   The system returns ``True`` if the data has been witnessed, ``False``
   if not.

   ::

    >>> repo_test.check_log(dt, b'roast')
    False

   The exact time is not necessary. A sufficiently approximate time is
   acceptable:

   ::

    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 11), c)
    True
    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 12), c)
    True
    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 13), c)
    True
    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 14), c)
    True
    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 15), c)
    False
    >>> repo_test.check_log(datetime.datetime(2101, 12, 25, 22, 9), c)
    False

   By default, a window of five seconds is given to all witnessings.

Adjusting Time Resolution
*************************
The required time accuracy for verifying witnessings, or the
*Time Resolution* can be adjusted as follows, given that ``repo_test``
from the guide above has been prepared:

 ::

  >>> repo_test.set_config({'time_res_s': 30})
  datetime.datetime(2101, 10, 5, 2, 51, 30)

The ``time_res_s`` (time resolution in seconds) value adjusts the
width of the time window.

Recall that the configuration herein was encoded in a Python ``dict``.

Configuration changes do not take place immediately; the datetime
returned after issuing ``set_config()`` is the time from which the new
configuration applies.

Acceptable ``time_res_s`` values are whole-number dividends of 86400,
including 86400 (well, because ``86400/1 == 86400`` 🤓).

PROTIP: The list comprehension ``[x for x in range(1, 86401) if 86400%x==0]``
contains all acceptable values for ``time_res_s``.

In-Memory Mode
**************
To avoid creating a database file in storage, simply leave out the
``db_path`` option:

 ::

   >>> repo_test = SQLiteRepository()

Hasher Tunables for Speed or for Confidentiality
************************************************
TODO: The hashing process during witnessing can be adjusted for speed
or for confidentiality. Document how to do this.

Weakness in Handling Unicode-Obfuscated Text
********************************************
If the text was obfuscated using alternate glyphs, decorations such as
overlapping marks or other Unicode formatting features (see *Lunicode*
for an example), the exact form has to be used for the verification to
succeed.

Unicode obfuscation may be used by adversaries as an effective
circumvention technique to frustrate verification. A proposed mitigation
would involve preprocessing the text to normalise its representation to
de-obfuscate it before its witnessing.

Can I Run The Unit Tests?
=========================
By all means, yes! Just run:

::
  
    python -m unittest

In the same directory as the repository. Due to their implementation,
you may find the tests slow. The entire test suite took about two minutes
to finish on a low-end, late 2010s vintage PC.

Hungry For More?
================
Whoa, that was unexpected, but thanks for your interest!
For deeper insights on how Muteacle works, please have a look at the
lone main module ``muteacle.py``. Pretty much any other module in
this project at this time is a test module.

Rationale (and some Fun Facts)
==============================
Muteacle was an attempt at *confidentiality-preserving data retention*
in high-confidentiality text messaging systems.

The shadow log system was a proposed solution to concerns of abuse
of high-confidentality messaging for facilitating unethical or criminal
intent. The method implemented herein preserves evidence of (mis-)use
which is intended to be accessible only via disclosure by a cooperative
defector.

First, the messaging system would witness the conversation, store it in
an irreversibly-encrypted (hashed) form and hold on to it for an agreed
period of time.

When evidence is needed to be presented, the defector is to turn in a
screenshot or any other record of conversation which contains (i)
the words of the conversation, and (ii) the time when the words were
communicated. While screenshots, voice readouts or other evidence can
be forged, especially with sophisticated machine learning techniques
(deepfakes), a shadow log aims to be able to verify the evidence.

*Muteacle* is a contraction of the phrase "The Mute Oracle", inspired by
the idea of an infinitely wise oracle who can answer any question, but
only with a *Yes* or a *No*. It has nothing to do with Oracle Corporation
or its products, but you are welcome to adapt it to use Oracle databases
to store the shadow logs...

