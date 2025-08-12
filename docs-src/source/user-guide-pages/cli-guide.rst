*************
CLI Guide
*************

This guide provides an in-depth introduction to the CLI and some caveats that are important to note to take advantage of all the features ``CEMENTO`` offers. If you just want to convert files, go to :doc:`Quick Start </quickstart>`.

Command Line Interface
======================

Once the package is installed, you will have access to a cemento CLI command for converting files. This CLI interface allows you to convert rdf triple files into draw.io diagrams and vice versa. To do convert from a turtle:

.. code-block:: console

    # converting from .ttl to drawio
    (.venv) $ cemento ttl_drawio your_triples.ttl your_output_diagram.drawio

    # converting from .drawio to .ttl
    (.venv) $ cemento drawio_ttl your_output_diagram.drawio your_triples.ttl

To convert from any other format (including turtle), use cemento ``rdf_drawio``. You can either use the appropriate file extension, or specify the format using the ``-f`` flag:

.. code-block:: console

    # converting from .xml to drawio
    (.venv) $ cemento rdf_drawio your_triples.xml your_output_diagram.drawio

    # alternatively, specify the format
    (.venv) $ cemento rdf_drawio -f xml your_triples.xml your_output_diagram.drawio

To convert from drawio to rdf triples, use the inverse functions ``drawio_ttl`` or ``drawio_rdf``:

.. code-block:: console

    # converting from .drawio to .ttl
    (.venv) $ cemento drawio_ttl your_output_diagram.drawio your_triples.ttl

    # converting from .drawio to .xml
    (.venv) $ cemento drawio_rdf your_output_diagram.drawio your_triples.xml

    # alternatively, specify the format
    # converting from .drawio to .xml
    (.venv) $ cemento drawio_rdf -f xml your_output_diagram.drawio your_triples.xml

It is that simple. In case you do need help, the CLI already comes with useful help pages. Just use the ``--help`` flag on the command or any of its subcommands:

.. code-block:: console

    (.venv) $ cemento --help
    (.venv) $ cemento drawio_ttl --help
    (.venv) $ cemento ttl_drawio --help
    (.venv) $ cemento drawio_rdf --help
    (.venv) $ cemento rdf_drawio --help

.. _supported-formats:

Supported Formats
-------------------

``CEMENTO`` uses ``rdflib`` under the hood so it supports any ``rdflib``-serializable format. Here is a table taken from the rdflib docs (v7.1.4). The **Keyword** column contains all your options for the ``-f`` flag:

.. list-table:: CEMENTO-supported RDF File Formats. Retrieved from `rdflib docs <https://rdflib.readthedocs.io/en/stable/intro_to_parsing.html#saving-rdf>`_ (as of v7.1.4)
   :name: cemento-supported-formats
   :header-rows: 1

   * - RDF Format
     - Keyword
     - Notes
   * - Turtle
     - turtle, ttl, or turtle2
     - turtle2 is just turtle with more spacing & linebreaks
   * - RDF/XML
     - xml or pretty-xml
     - Was the default format, rdflib \< 6.0.0
   * - JSON-LD
     - json-ld
     - There are further options for compact syntax and other JSON-LD variants
   * - N-Triples
     - ntriples, nt, or nt11
     - nt11 is exactly like nt, only utf8 encoded
   * - Notation-3
     - n3
     - N3 is a superset of Turtle that also caters for rules and a few other things

If the format flag ``-f`` is not provided, ``CEMENTO`` automatically infers the format based on the file extension. If you want to output a file with a different extension or specify a more specific format for the same file-type, please set the format explicitly with ``-f``.

.. _term-matching:

Term Matching
=============

When converting from draw.io to ``.ttl``, your draw.io diagrams can have classes, instances, or predicates that can correspond with those in a reference ontology like CCO or PMDCO. To avoid redundancy, ``CEMENTO`` automatically matches them for you. This section describes how it does so, but only from the perspective of CLI use. If you want to learn more about diagram drawing, please refer to the :doc:`Drawing Basics Section </user-guide-pages/drawing-basics>`.

Acceptable Format for Term Matching
-----------------------------------

A term in a diagram is only matched if it is on a shape or an arrow label. They can have the following format:

.. code-block:: python

    <prefix>:<abbrev-term>

    # for example
    cco:ICE

Where, ``<prefix>`` is the prefix the reference ontologies used to refer to that term. ``<abbrev-term>`` can either be the last part of the term URI, its label, or one of its alternate labels (``rdfs:label`` or ``skos:altLabel``).

For example, CCO's ``Information Content Entity`` has a URI of ``https://www.commoncoreontologies.org/ont00000958`` so you can write ``cco:ont00000958`` (with the last part of the term URI), ``cco:Information Content Entity`` (with the ``rdfs:label`` value), or ``cco:ICE`` (with a known ``skos:altLabel`` value).

Your terms do not have to be the exact copy of the IRI or the label of the term you want to match. ``CEMENTO`` automatically adds the aliases of the referenced terms to its search-pool in addition to conducting *fuzzy-search* to get matches. Hence, you can use symbols like spaces, underscores, or dashes if you wish. A word of caution with camel case or pascal case though. They are usually standard but they are harder to match. Use them with discretion.

Beware, shorter terms are also harder to match, and only aliases inside the reference ontologies will be used. For example, ``cco:ICE`` will match to "Information Content Entity" in the CCO ontology. In contrast ``cco:Information CE`` will not match because it is not a known ``skos:altLabel`` or ``rdfs:label`` of  the term.

Terms that are replaced will have the ``skos:exactMatch``  relationship to the term they reference. Since the term is replaced, this will be a self-referential triple added just for annotation.

.. _def-ref-ontos:

Default Reference Ontologies
----------------------------

By default, the program compiles with the versions of the reference ontologies it needs to do term matching. Specifically, it comes bundled with the following ontologies.

* `Common Core Ontologies <https://github.com/CommonCoreOntology/CommonCoreOntologies>`_
* `OWL Schema <https://www.w3.org/2002/07/owl#>`_
* `RDF Schema <https://www.w3.org/1999/02/22-rdf-syntax-ns#>`_
* `RDFS Schema <https://www.w3.org/2000/01/rdf-schema#>`_

These ontology files are used by CEMENTO for referencing terms and predicates. The package has built-in copies of the reference files in the ``.ttl`` format. As you can imagine, the default reference ontology is CCO, which is the preferred mid-level ontology by the SDLE center. The next section details how you can add your own reference ontologies.

Adding or Replacing Reference Ontologies
=========================================

The ``cemento ttl_drawio`` and ``cemento rdf_drawio`` commands have an argument called ``--onto-ref-folder-path`` which you can point to a folder containing the RDF files that contain the terms you want to reference. For example, you can download a ``.ttl`` file from the official CCO repo page and place it here to reference all CCO terms. In the package implementation, this referencing is additive, which means you can add as many RDF files as you want to reference. By default, cemento will already come bundled with this folder, but it will currently only reference CCO.

    | **CAUTION:** Repeated references are overwritten in the order the files are read by python (usually alphabetical order). If your reference files conflict with one another, please be advised and resolve those conflicts first by deleting the terms or modifying them in the RDF files.

Replacing Default Ontologies
-----------------------------

The schemas for RDF, XML, and RDFS contain the terms that all ontologies ought to understand by default. Thus, a lot of assumptions were made surrounding their standard use during the development of the package. You can, however, also specify a folder of choice through the ``--defaults-folder-path`` option for ``cemento ttl_drawio`` and ``cemento rdf_drawio``. Replace it at your own risk.

.. _custom-terms-prefixes:

Custom Terms and Prefixes
=========================

Creating new terms is just as easy as adding them. However, using custom namespaces is a different matter. Any term that doesn't come with a prefix gets assigned our default namespace `mds <https://cwrusdle.bitbucket.io/>`_.

In order to use custom prefixes, you need to create a ``prefix.json`` file that looks like the following:

    | **NOTE:** This exact file is available when you :ref:`pull the repository <install-from-repo>` and can be found in ``examples/prefixes.json``.

.. code-block:: json

    {
        "cco": "https://www.commoncoreontologies.org/",
        "mds": "https://cwrusdle.bitbucket.io/mds/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "ncit": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "obo": "http://purl.obolibrary.org/obo/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "qudt": "http://qudt.org/schema/qudt/",
        "pmdco": "https://w3id.org/pmd/co/",
        "pmd": "https://w3id.org/pmd/co/",
        "dcterms": "http://purl.org/dc/terms/",
        "unit": "http://qudt.org/vocab/unit/",
        "afe": "http://purl.allotrope.org/ontologies/equipment#",
        "afm": "http://purl.allotrope.org/ontologies/material#",
        "afq": "http://purl.allotrope.org/ontologies/quality#",
        "afr": "http://purl.allotrope.org/ontologies/result#"
    }

This file is just a python dictionary enclosed as a ``json`` object. Add yours by following the format (copy-paste a line, for example) and inserting it at the bottom of this file. Make sure your prefix is reasonably unique (i.e. don't copy one that is already in this file).

After you are happy with your file, go ahead and set the ``--prefix_file_path`` when running cemento ``cemento drawio_ttl`` or ``cemento drawio_rdf``. **Point the argument it to the path to your file**. It should now read your custom prefixes and add the right namespace for your terms.