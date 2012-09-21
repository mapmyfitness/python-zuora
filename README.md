python-zuora
============

Overview
--------
This is a simple client designed to communicate with Zuora via Python Suds.

Dependencies
------------
Right now, the client's primary dependency is on a patched version of
the Suds library.

Hopefully that will change soon.

Usage
-----
Using the client is fairly simple:

    $ pwd
    /usr/local/project/python-zuora
    $ python
    ...
    >>> # Get a new client with the default host and path.
    >>> import zuora
    >>> zuora_settings = {'username': 'example_user',
    >>>                   'password': 'example_pass',
    >>>                   'wsdl_file': 'zuora.a.39.0.dev.wsdl'}
    >>> z = zuora.Zuora(zuora_settings)
    >>> z.get_account(user_id=1232)

Be sure to replace usernames and passwords with your own values.

Running tests locally is as simple as:

    $ py.test --pdb -v python-zuora/zuora/tests.py

Advice for maintainers
----------------------
Maintainers should strive not to include any proprietary information. The client
should also present a clean interface. Please be ruthless about explicitness and
code legibility.
