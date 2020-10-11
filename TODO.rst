Wishlist
--------

0.1.2
=====

Tests
*****
* **Invalid System Clock Handling**: test cases for SQLiteRepository
  when multiple pending repository configurations are detected.

* **SQLite Repository DB Operations**: Private methods that handle
  database operations. These methods have names beginning with
  ``_slr``.

Maintenance
***********
* **``muteacle``**: Main module docstrings need to be finished.

* **Routine maintenance**

  * Use clearer local variable names.

  * Improve consistency of terminology in variable names, docstrings
    and comments.

0.1.3
=====

Features
********
* **Datetime Faking**: Important for testing and predicting long-term
  behaviours of Repositories. Tests may also become faster if this
  feature eliminates the need to wait for intervals to pass during
  testing.

* **Repository**

    * ``default_hasher_class()``: shortcut for getting the default
      hasher class without a multi-stage lookup routine

    * ``get_latest_hasher()``

    * ``sleep_until_repo_config_applied()``, alternative to
      ``sleep_until_interval_end()`` that senses when pending
      Repository configurations have been applied

Beyond
======

Documentation
*************
The following need to be addressed:

* Use Cases

* Accuracy of negatives and positives

* Preservation of Data Confidentiality

* Performance and suitability of existing database backends

* Potential weaknesses and mitigations

* Social and legal issues and acceptance

Miscellaneous Wishlist
**********************
* **Flexible Timestamping**: It may be possible to store witnessings
  in a way where the time resolution can be applied immediately, and
  retroactively. Currently, the time resolution cannot be changed for
  witnessings already written to the database.
  
  * Retroactive changes to time resolution may be desired for some
    use cases, but might also cause data confidentiality issues.

* **Handling of Slow Hasing Operations**: Hashing operations that take
  more than one interval to complete have not been tested. Tests that
  ensure hashes that take a long time to generate are correctly logged
  would be nice.

* **Re-hashing**: Ability to upgrade hashes to a more secure standard
  as they become available or necessary, while protecting recallability
  of the hashes

