**************
Drawing Basics
**************

The ``CEMENTO`` package can take any single or multi-page draw.io file and process it. However, parsing it *properly* to get the right RDF triples is a different matter. This guide goes through some things for you to keep in mind so your diagrams actually correspond with your ``.ttl`` outputs.

Drawing with draw.io
====================

If you have not used draw.io before, please refer to their comprehensive tutorials `here <https://drawio-app.com/tutorials/>`_. Where you draw your draw.io doesn't really affect the package performance as long as ``CEMENTO`` has access to the output ``.drawio`` file. Once you are familiar with the basics of ``.drawio``, there are a few additional things to note:

* Use the ``.drawio`` file extension for your diagram! This is to avoid ambiguity between RDF/XML files and your diagrams.
* You can use any **simple** shape for your classes, literals and instances. **HOWEVER**, any shape you put (including textboxes) will be considered a class, literal or instance.
* You draw predicates with arrows. Please make sure that your arrows actually connect to the shape and not just look as if it does.
* Your arrows must be drawn from source to target. **Your arrows must be end-arrow only.**
* Predicate labels must be done on the arrow itself. Putting a box on top of an arrow will not work. Only one label per arrow.
* Literals must come with double-quotes regardless of data type. Avoid using nested double-quotes.
* You can draw a shape with the text 'A-Box' or 'T-Box' and a line without a label for annotations. Everything else is treated as part of the ontology.

A Walkthrough
=============

The following diagram goes through an example supplied with the repository called ``happy-example.drawio`` with its corresponding ``.ttl`` file called ``happy-example.ttl``. We used CCO terms to model the ontology, so please download that file and place it into your :ref:`ontology reference folder <def-ref-ontos>` so you can follow along.

.. iframe:: https://viewer.diagrams.net?#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FGabbyton%2FCEMENTO%2Frefs%2Fheads%2Fmaster%2Ffigures%2Fdo-not-input-this-happy-example-explainer.drawio
    :height: auto
    :width: 100%
    :aspectratio: 1.77

Having trouble? Download the figure above as an :download:`svg image <https://raw.githubusercontent.com/Gabbyton/CEMENTO/refs/heads/master/figures/happy-example-explainer.drawio.svg>` or :download:`draw.io diagram <https://raw.githubusercontent.com/Gabbyton/CEMENTO/refs/heads/master/figures/do-not-input-this-happy-example-explainer.drawio>`.

In Case You Missed It
=====================

The diagram above goes through all that you need to know to start making diagrams you can convert to RDF files (Isn't that cool?); but in case it wasn't obvious, here is a summary of features you can leverage that ``CEMENTO`` will understand:

* **Term matching.**
    Any term and predicate you create will be matched with a term. Just make sure to use the right prefix. More details :ref:`here <term-matching>`.

* **Shorthand aliasing.**
    You can add labels and alt-labels to your term by simply adding them parenthetically. For example: ``mds:MyCustomTerm (my label, my alt label)``. The first term in the comma-separated series is always the label. Any subsequent terms are alt-labels (No language support yet).

* **Match suppression.**
    If you don't want a term substituted or matched, just add an asterisk to the name (\*).

* **Custom terms and prefixes.**
    New terms without prefixes will be matched with our default namespace, **mds**. To add a custom prefix, just use the prefix, but add it to a ``prefixes.json`` file (how to do that :ref:`here <custom-terms-prefixes>`).

* **Literal languages and data types.**
    Just write your value the way you would write it in turtle, i.e. ``"Happy Gilmore"^^xsd:string`` or ``"Happy Gilmore"@en`` to define datatypes and set a language respectively.

        | **NOTE:** The package now supports imported datatypes! Locally defined (same-file) datatype definitions are not supported yet.