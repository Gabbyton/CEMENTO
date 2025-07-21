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

**Version:** |release|

**Useful links**:
`Source Repository <https://github.com/Gabbyton/CEMENTO>`_ |
`Issue Tracker <https://github.com/Gabbyton/CEMENTO/issues>`_ |
`MDS-Onto Website <https://cwrusdle.bitbucket.io>`_


What is CEMENTO?
===============

CEMENTO stands for the Centralized Entity Mapping & Extraction Nexus for Triples and Ontologies -- a mouthful, but an important metaphor for the package building the road to ontologies for materials data.This package is part of the larger SDLE FAIR application suite that features tools to create scientific ontologies faster and more efficiently. This package provides functional interfaces for converting draw.io diagrams of ontologies into RDF triples in the turtle (`.ttl`) format and vice versa. This package is able to provide term matching between reference ontology files and terms used in draw.io diagrams allowing for faster ontology deployment while maintaining robust cross-references.

.. grid:: 2
   
    .. grid-item-card::
        :img-top: _static/running_person.svg

        Quick Start
        ^^^^^^^^^^^

        You just want to convert files? Check out our quick start guide to take you through the CEMENTO cli and convert ontology diagrams like a pro.

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

            To the user guide

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`