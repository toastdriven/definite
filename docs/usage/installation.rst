Installation
============

You must be running Python 3.6 or greater.

`definite` only requires the Python built-in standard library & has no
other dependencies.


Standard Installation
---------------------

For everyday usage, simply run::

    $ pip install definite

It's recommended that you use a `virtualenv` (or `poetry`, or `pipx`, or
whatever) to isolate your install from the system Python.


Development Installation
------------------------

If you'd like to work on `definite`'s code, run tests or generate the docs
locally, the setup is a touch more complex. Here's the recommended approach.

::

    $ git clone git@github.com:toastdriven/definite.git
    $ cd definite
    $ poetry install
    $ poetry shell

    # Now you can run tests.
    $ pytest .

    # Or build the docs.
    $ cd docs
    $ make html && open _build/html/index.html