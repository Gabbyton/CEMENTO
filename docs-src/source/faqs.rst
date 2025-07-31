****
FAQs
****

This page documents questions or issues that have come frequently during our package use and development. It is divided into sections pertaining to the category of your question. Please refer to this page first prior to creating an issue, whose instructions are found at the very bottom.

Package Installation
=====================

.. dropdown:: How do I install the package?

    Install using `pip <https://pypi.org/project/pip/>`_: ``pip install cemento``.

.. dropdown:: I have the right python version but I get ``error: externally-managed-environment``. How do I install the package?
    
    This means you are currently not installing CEMENTO in a virtual environment. Please check our :ref:`guide section <use-venv>` for installing virtual environments, or refer to `python's instructions <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_.

.. dropdown:: What is the minimum python version to use the package?

    To use the **latest** version of the package, please upgrade your python to version ``>=3.10``. Installing with python 3.8 wil yield an error. Installing with python 3.9 will work but you will be using our OOP-based iteration instead of the supported latest version. Also, we do recommend upgrading your version regardless of your interest in CEMENTO. Python 3.9 is nearing its `end-of-life <https://devguide.python.org/versions/>`_ for security and package support.

.. dropdown:: I can install the package in python 3.9 but the CLI is not working?

    Installing CEMENTO on python version 3.9 will give you the old module-only OOP-based iteration of the package that does not come with the CLI. Please upgrade your python to 3.10 or above and try again.

Usage
======

.. dropdown:: How do I convert my diagram into an RDF format that is not turtle?

    We are planning to have this option in an upcoming release. For now, it's important to note that we use the ``rdflib`` library under the hood to perform operations. Thus, you can use ``rdflib`` to convert our turtle output into any other ``rdflib``-supported format.

.. dropdown:: I am using the CLI to convert my drawio diagram to a turtle file but it gives me ``BadDiagramError``. How do I fix it?

    This error means there are simple but critical errors that are related to how you draw your diagram. Please scroll up to see the list of errors. Incurring an error will also spit out a copy of your file with errors in red. The file will be saved in the same folder as your input with the ``error_check`` added to the name.

.. dropdown:: I am trying to look for the red error element in my error-check file but I can't see it. How do I find the error?

    This is often the case when a label or other element is covering up the erring element (which is often too small to see). Check the error output from your terminal and scroll up to find the entire list of errors. This list will always provide the ID and location or the location of connected terms. To reference the location, activate the ruler in your drawio app via the ``View`` menu, then check ``Ruler``. If you only have the ID, open your drawio file with a text editor and search for the ID. It will direct you to the code of the erring element.

.. dropdown:: I fixed the errors in my error check file but I still get the same errors when running the program again. Any guidance?

    Make sure the CLI or script input path now points to the error check file. We do not overwrite to your file by default to maintain your file version. If you do point to the error check file, we will write directly to that file instead to allow for iterative error fixing.

.. dropdown:: The package is complaining about non-ontology elements I add in my diagram (e.g. legends, lines, T-box, A-box, etc.). Is this correct?

    Yes, For flexibility, CEMENTO treats any simple shape as a term, and any arrow as a triple definition. Please avoid annotation symbols in your final input. We are currently implementing exemptions so we will update users in our documentation for renewed annotation guidance.

.. dropdown:: How do I add axioms and restrictions?

    This version of the package does not currently support axioms and restrictions. We are still searching for a way to define them visually that is most appropriate and clear for domain scientists. We found the solution provided by the `Chowlk <https://github.com/oeg-upm/Chowlk>`_ package to be elegant (using element pallettes) but doing so limits users to developer-defined capabilities rather than catering to OWL/RDF syntax globally. Thus, we would rather find a working design solution first instead of implementing what they already have and duplicating their work.
    
    If axioms are crucial, please defer to that project instead. It does what we do but without term matching, and it requires server setup for local deployment.

    Another alternative is `OWLAx <https://github.com/md-k-sarker/OWLAx>`_ which also does what we do and is integrated into the `Protégé <https://protege.stanford.edu/>`_ software application as a  plug-in. This package won't take a draw.io as input, but they do have an interface for drawing ontology diagrams.

Inaccurate outputs
====================

.. dropdown:: Using the CLI, I managed to convert my diagram to turtle, but the output file contains unfamiliar terms that replaced my own?

    Our package uses fuzzy search to perform term matching, and the term you used was too close to a preexisting term. For example, ``yourprefix:dateTime`` is still going to match with ``xsd:dateTime``. If you don't want this behavior, add an asterisk (*) to your term name. To track substitutions, use the ``-lsp`` option on the CLI command.

.. dropdown:: I managed to convert my diagram to turtle, but I notice  some of my triples are inverted?

    First of all, check that your diagram connects the right way. Second, check that the end and start arrows are set properly. Triple arrows are only supposed to have an end-arrow. To verify your arrow, click on it and open the Style tab on the right-hand pane. You must have the same arrow configuration as shown in the yellow box below. Sometimes, draw.io will just invert this automatically and the option to turn it off is not known to us. This aspect of draw.io is out of our control. Please register a feature suggestion or report a problem with the draw.io people if you wish.

    .. image:: /_static/faq-end-start-arrows.png
        :width: 400
        :alt: Start arrow must be None (left), end arrow must be set

.. dropdown:: I managed to convert my diagram to turtle, but the output file is listing instances as classes or vice versa?
    
    This error is because you used the same exact instance name as your class name. We understand this may be common in tutorials (and most often, not standard practice), but unless you assign a custom prefix to your instance name, your class and your instance will resolve to the same IRI. Please consider renaming your terms to be distinct.

.. dropdown:: I managed to convert my diagram to turtle, but the output file contains domains and ranges that assign to instances. Is this correct?

    This is by design but this is not correct. We are currently developing algorithms for class inference based on the collected instances, so we only collect instances for now. This addition only occurs for custom object properties that were not matched by the package. You are free to edit the turtle with the classes you actually want to include. You are also free to just remove them. We will set up an option to turn this feature off in an upcoming release.

Documentation page issues
===========================


.. dropdown:: I managed to convert my diagram to turtle, but the documentation I generate with `widoco <https://github.com/dgarijo/Widoco>`_ or `PyLode <https://github.com/RDFLib/pyLODE>`_ names my classes as instances?

    This was a known internal issue at our lab. We found out this is because some class definitions get assigned object properties, or a referenced class had inverted ``rdf:subClassOf`` or ``rdf:type`` triples. If you think this is because of CEMENTO, please open an issue. In any case, please proceed to move those triples to the appropriate subjects and objects.

.. dropdown:: I managed to convert my diagram to turtle, but the documentation I generate with `widoco <https://github.com/dgarijo/Widoco>`_ or `PyLode <https://github.com/RDFLib/pyLODE>`_ names my reference terms as subclasses of my custom terms?

    Check that your arrows are not inverted when declaring ``rdfs:subClassOf`` or ``rdf:type``. This, from our experience, is usually the issue.

Citation
=========

.. dropdown:: I found your package to be very useful. How do I cite it for my publication?

    Thank you for using our package and we are glad it helped. Please check our :ref:`about page <cite-work>` for information about citing the project.

Issue Reports and Contributions
================================

.. dropdown:: How do I report an issue with the package?

    Please refer to our official github issue tracker at `<https://github.com/cwru-sdle/CEMENTO/issues>`_. Please provide a detailed description of your error and your system information (if you think it's relevant). Attach your turtle or diagram file if possible, or a contrived example that reproduces your error. Please be respectful. Remember this package is free and open source.

.. dropdown:: I want to contribute to the package or make my own. Do you have suggestions?

    Feel free to create a pull request but associate it with an issue for proper documentation. Please check our user guide section :ref:`on using modules <module-structure>` for information about how the package is structured. You are also welcome to fork the project. Please make sure to abide by :ref:`project-license`.