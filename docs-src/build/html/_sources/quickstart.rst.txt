***********
Quickstart
***********

    | **NOTE:** It is recommended you install in a python environment. If you do not know how to set up a virtual environment, please refer to :ref:`this link <use-venv>` or check out `python's instructions <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_.

Before converting
==================

Install cemento with pip.

:bdg-danger:`warning` The ``CEMENTO`` package only supports python versions ``>=3.10``.

.. code-block:: console

    (.venv) $ pip install cemento


Run the following to see if it's properly installed:

.. code-block:: console

    (.venv) $ cemento --help

It should show the following:

.. image:: /_static/good-output.png
    :width: 500px

Download the Example
--------------------

Clone the official repo to get the example. Prefer the master branch:

.. code-block:: console

    (.venv) $ git pull https://github.com/Gabbyton/CEMENTO.git
    (.venv) $ cd CEMENTO/examples/

There should be two files ``happy-example.drawio`` and ``happy-example.ttl``

Converting from draw.io to ``.ttl``
-----------------------------------

Inside the ``examples`` folder, run the following command:

.. code-block:: console

    (.venv) $ cemento drawio_ttl happy-example.drawio sample.ttl

| **NOTE:** Paths can be absolute or relative.

Converting from ``.ttl`` to draw.io
------------------------------------

Similar to the above, run the following command:

.. code-block:: console

    (.venv) $ cemento ttl_drawio happy-example.ttl sample.drawio

Help message
-------------

If you get lost, there is always:

.. code-block:: console

    (.venv) $ cemento --help
    (.venv) $ cemento drawio_ttl --help
    (.venv) $ cemento ttl_drawio --help

Check output
-------------

Congratulations! If you made it to this point, you've managed to convert your files from draw.io to ``.ttl`` and back. Compare the results you get with those in ``happy-example.drawio`` and ``happy-example.ttl`` respectively. Note that the diagram will not be the exact same look, but the connections and terms should all be the same.

What now?
-----------

You can now start converting YOUR diagrams from draw.io to turtle format and vice versa! To read more about other cool features, start with the :doc:`User Guide </user-guide>`.