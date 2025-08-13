*************
Installation
*************

Installing the package is as easy as using ``pip install``, However there are a few considerations that are detailed on this section. Please refer to prerequisites prior to installing the package.

Prerequisites
=============

#. **Python Version.** This package requires python installed at version ``>=3.10``. Lower versions will not work. If you really need to maintain a lower version, please check the versioning guide (pending), to modify the code to remove modern python features.
#. **draw.io app.** Though not strictly required by the package, a draw.io application, either installed on your computer or online will allow you to create and edit examples as well as make your own ontology diagrams.
#. **A plain-text file editor.** Same as the above, this tool can be a simple notepad or complex IDE that you can use to check `.ttl` files. If your computer does not recognize the format, please make sure to set it to open on your file editor of choice.

Installing via ``pypi``
=======================

To install this particular package, use pip to install the latest version:

.. code-block:: console

    (.venv) $ pip install cemento

.. _use-venv:

We recommend a python environment to prevent dependency conflicts:

.. code-block:: console

    (.venv) $ python -m venv <env-name>

You choose the environment name ``<env-name>``. We recommend either ``.venv`` or ``.CEMENTO``.

Feel free to use non-native environment managers like `conda <https://anaconda.org/anaconda/conda>`_ and `mamba <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>`_. As long as yours has access to ``pypi``, you are good to go.

**NOTE:** The ``pip install`` will download the latest available version of the package. If you found our package on ``pypi``, beware of major version changes. This documentation only covers versions above ``v8.4``. Any versions below use an OOP-based interface which these docs don't cover.

.. _install-from-repo:

Installing from the Repository
==============================

If you wish to use the development version of the package, please feel free to pull the repository and install the package locally via:

.. code-block:: console

    (.venv) $ git pull https://github.com/Gabbyton/CEMENTO.git
    (.venv) $ cd CEMENTO/examples
    (.venv) $ pip install -e .

The command ``pip install -e .`` will look for any packages in your project repo folder and install them in *development mode.* This means that any changes you make on the actual package, the ``cemento`` folder, will be reflected on the installed package. After doing so, you will already have access to the ``cemento`` keyword on your terminal.

Branches
--------

The repository currently has two denominated branches that will be in active development:

* ``main`` hosts the versions that will be sourced for building the actual ``CEMENTO`` package. They also contain documentation since all functions are assumed to be final. We take advantage of git tags to track versions.
* ``dev`` is the most recent ``HEAD`` of the repo containing the most recent changes. These do not contain documentation and are highly unstable. Please pull from this branch at your own risk.