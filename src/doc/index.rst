.. Environment Editor documentation master file, created by
   sphinx-quickstart on Mon Sep  7 12:29:04 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Environment Editor's documentation!
==============================================

Contents:

.. toctree::
   :maxdepth: 2

* Allows viewing of environment variables (editing in a future version)
* Tkinter interface

Configuration schemes
---------------------

* bash
    * :file:`/etc/profile` (system)
    * :file:`/etc/bashrc` (system)
    * :file:`/etc/bash.bashrc` (system, ubuntu)
    * :file:`/etc/environment` (pam)
    * :file:`~/.bashrc` (non login)
    * :file:`~/.bash_profile` (login)
    * :file:`~/.bash_login` (login)
    * :file:`~/.profile` (login)

* csh
    * :file:`/etc/csh.login`
    * :file:`/etc/csh.cshrc`
    * :file:`~/.tcshrc`
    * :file:`~/.cshrc`

* `fish <http://fishshell.com/docs/current/index.html#variables>`_

* Windows
    * Registry
    * REG_EXPAND_SZ for vars with %VAR% 
    * REG_SZ for the others

Variable Locations

* System
* User
* Current

Notes
-----

login shell - machine startup, user session startup, ssh shell

interactive shell - terminal app, ssh shell

env variables set by script, name=value file 


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

