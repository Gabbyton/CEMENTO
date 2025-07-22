**************
Drawing Basics
**************

The ``CEMENTO`` package can take any single-page draw.io file and process it. However, parsing it *properly* to get the right RDF triples is a different matter. This guide goes through some things for you to keep in mind so your diagrams actually correspond with your ``.ttl`` outputs.

A Walkthrough
=============

The following diagram goes through an example supplied with the repository called ``happy-example.drawio`` with its corresponding ``.ttl`` file called ``happy-example.ttl``. We used CCO terms to model the ontology, so please download that file and place it into your :ref:`ontology reference folder <def-ref-ontos>` so you can follow along.

.. iframe:: https://viewer.diagrams.net?#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FGabbyton%2FCEMENTO%2Frefs%2Fheads%2Fmaster%2Ffigures%2Fdo-not-input-this-happy-example-explainer.drawio
    :height: auto
    :width: 100%
    :aspectratio: 1.77

Having trouble? Download the figure above as an :download:`svg image <https://raw.githubusercontent.com/Gabbyton/CEMENTO/refs/heads/master/figures/happy-example-explainer.drawio.svg>` or :download:`drawio diagram <https://raw.githubusercontent.com/Gabbyton/CEMENTO/refs/heads/master/figures/do-not-input-this-happy-example-explainer.drawio>`.

In Case You Missed It
=====================

The diagram above goes through all that you need to know to start making diagrams you can convert to ``.ttl`` files (Isn't that cool?); but in case it wasn't obvious, here is a summary of features you can leverage that ``CEMENTO`` will understand:

* **Term matching.**
    Any term and predicate you create will be matched with a term. Just make sure to use the right prefix. More details :ref:`here <term-matching>`.

* **Match suppression.**
    If you don't want a term substituted or matched, just add an asterisk to the name (\*).

* **Custom terms and prefixes.**
    New terms without prefixes will be matched with our default namespace, **mds**. To add a custom prefix, just use the prefix, but add it to a ``prefixes.json`` file (how to do that :ref:`here <custom-terms-prefixes>`).

* **Literal languages and data types.**
    Just write your value the way you would write it in turtle, i.e. ``"Happy Gilmore"^^xsd:string`` or ``"Happy Gilmore"@en`` to define datatypes and set a language respectively.

        | **NOTE:** The package only currently support `XSD datatypes <http://www.w3.org/2001/XMLSchema#>`_ as is the standard practice for this notation.