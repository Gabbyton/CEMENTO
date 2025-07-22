.. CEMENTO documentation master file, created by
   sphinx-quickstart on Mon Jul 21 10:58:46 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***********
CEMENTO
***********

.. toctree::
   :maxdepth: 1
   :hidden:

   quickstart
   user-guide
   modules

**Version:** |release|

**Useful links**:
`Source Repository <https://github.com/Gabbyton/CEMENTO>`_ |
`Issue Tracker <https://github.com/Gabbyton/CEMENTO/issues>`_ |
`MDS-Onto Website <https://cwrusdle.bitbucket.io>`_ |
`PyPI Page <https://pypi.org/project/cemento/>`_



CEMENTO is a component python package of the larger **SDLE FAIR application suite** of tools for creating scientific ontologies more efficiently. This package provides functional interfaces for converting draw.io diagrams of ontologies into RDF triples in the turtle (`.ttl`) format and vice versa. This package is able to provide term matching between reference ontology files and terms used in draw.io diagrams allowing for faster ontology deployment while maintaining robust cross-references.

CEMENTO stands for the Centralized Entity Mapping & Extraction Nexus for Triples and Ontologies -- a mouthful for an acronym, but an important metaphor for the package building the road to ontologies for materials data.

.. grid:: 2
   
    .. grid-item-card::
        :img-top: _static/running_person.svg

        Quick Start
        ^^^^^^^^^^^

        You just want to convert files? Check out our quick start guide get your started converting ontology diagrams and ``.ttl`` files.

        +++

        .. button-ref:: quickstart
            :expand:
            :color: dark
            :click-parent:

            To Quick Start

    .. grid-item-card::
        :img-top: _static/book.svg

        Guide
        ^^^^^

        A detailed guide for using the CLI and the scripting tools.

        +++

        .. button-ref:: user-guide
            :expand:
            :color: dark
            :click-parent:

            To the User Guide

    .. grid-item-card::
        :img-top: _static/more.svg

        API Reference
        ^^^^^^^^^^^^^

        The full documentation for all things CEMENTO.

        +++

        .. button-ref:: modules
            :expand:
            :color: dark
            :click-parent:

            To the API Reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`