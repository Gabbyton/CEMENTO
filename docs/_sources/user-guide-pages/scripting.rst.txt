*************
Scripting
*************

The package is composed of four main modules that can be imported into a python script. The following sections can show how to use the package for the its most common (and simplest) use-cases:

Converting draw.io to ``.ttl`` files
=====================================

Using the actual function is as easy as importing and calling it in a python script. The function takes the exact same arguments that you can set in ``cemento drawio_ttl``. In this case, the script needs to set those arguments explicitly.

.. code-block:: python

    from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl

    INPUT_PATH = "your_onto_diagram.drawio"
    OUTPUT_PATH = "your_triples.ttl"
    ONTO_PATH = "data" # this path points to the folder containing all the ttl files you want to reference (optional)
    DEFAULTS_FOLDER = "" # path to the folder containing default terms. It should come with the cloned repo (optional)
    PREFIXES_PATH = "prefixes.json" # this path points to a prefixes file with custom prefix assignments (optional)

    if __name__ == "__main__":
        convert_drawio_to_ttl(INPUT_PATH, OUTPUT_PATH, ONTO_PATH, DEFAULTS_FOLDER, PREFIXES_PATH)

Converting ``.ttl`` files to draw.io files
==========================================

This case is very similiar to the previous one. The ``.ttl`` was assumed to contain the necessary information so you only need to set the ``INPUT_PATH`` and ``OUTPUT_PATH``. The option and ``set_unique_literals`` determines whether tot treat literals with the same name as different things. ``horizontal_tree``, on the other hand, sets whether to draw tree diagrams horizontally or vertically.

.. code-block:: python

    from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

    INPUT_PATH = "your_triples.ttl"
    OUTPUT_PATH = "your_onto_diagram.drawio"

    if __name__ == "__main__":
        # the horizontal tree parameter controls whether you want the default vertical tree (False) or an inverted horizontal tree (True)
        convert_ttl_to_drawio(INPUT_PATH, OUTPUT_PATH, horizontal_tree=False, check_ttl_validity=True, set_unique_literals=True)

Converting draw.io to a ``networkx`` DiGraph
============================================

We used a directed networkx graph (DiGraph) as an intermediary data structure that provides a much richer interface for graph manipulation than the default ``rdflib`` Graph. If you are interested in using this data structure, you are free to use the functions shown below:


.. code-block:: python

    from cemento.draw_io.read_diagram import read_drawio
    from cemento.draw_io.rdf.turtle_to_graph import convert_ttl_to_graph

    DRAWIO_INPUT_PATH = "your_onto_diagram.drawio"
    TTL_INPUT_PATH = "your_triples.ttl"
    ONTO_FOLDER = "data"  # this path points to the folder containing all the ttl files you want to reference (optional)
    DEFAULTS_FOLDER = "defaults"  # path to the folder containing default terms. It should come with the cloned repo (optional)
    PREFIXES_PATH = (
        ""  # this path points to a prefixes file with custom prefix assignments (optional)
    )
    if __name__ == "__main__":
        # reads a draw.io diagram and converts it the graph
        graph = read_drawio(DRAWIO_INPUT_PATH, ONTO_FOLDER, PREFIXES_PATH, DEFAULTS_FOLDER)
        # use the graph here as proof
        print(graph.edges(data=True))

        #reads a ttl file and converts it to a graph
        convert_ttl_to_graph(TTL_INPUT_PATH)

In fact, the functions ``read_drawio`` and ``convert_ttl_to_graph`` are actually wrapped around to form the ``convert_ttl_to_drawio`` and ``convert_drawio_to_ttl`` functions. You are already using the former pair when using the latter.

Important Note on ``read_drawio``
----------------------------------

When using the ``read_drawio``, please exercise caution when providing the paths. The function has a signature:

.. code-block:: python

    read_drawio( input_path: str | Path, onto_ref_folder: str | Path = None, prefixes_folder: str | Path = None, defaults_folder: str | Path = None, relabel_key: DiagramKey = DiagramKey.LABEL, inverted_rank_arrow: bool = False)

If you aren't planning on leveraging stratified layouts like the ones used in ``draw_tree``, please supply just the arguments for ``input_path`` and optionally, ``relabel_key`` and ``inverted_rank_arrow``.

A Note on "Unique" Literals
---------------------------

By default, the package will not treat all literals as being unique from one another. Classes and instances, by design, have singular, unique IRIs so they are treated to be the same if drawn in multiple locations. By default, literals will be treated the same way even though they don't have unique IRIs.

To make unique literals (which don't come with IRIs), the package can append all literal terms with a unique ID that prevents merging. To do so, set the ``set_unique_literals`` argument when using the functions ``convert_ttl_to_drawio`` and ``convert_ttl_to_graph``.

You are free to remove them using ``remove_literal_id`` which is just one of the functions we wrote in ``cemento.draw_io.preprocessing``. You are also free to implement your own algorithm as well.

Using Other Modules
===================

This package was built along the paradigms of `functional programming <https://en.wikipedia.org/wiki/Functional_programming>`_ which is only possible in Python through a `hybrid approach <https://docs.python.org/3/howto/functional.html>`_. The modules are divided by four main logical groupings, and are as follows:

#. ``cemento.cli``
    This module contains code with the CLI interface definitions.
#. ``cemento.draw_io``
    This module has code that parses, reads and converts draw.io diagrams of ontologies into ``networkx`` DiGraph objects (with proper formatted content) and vice versa. The content generated here is subsequently used in the ``rdf`` module.
#. ``cemento.rdf``
    This module handles the conversion of ``draw.io`` to ``.ttl`` and vice versa. It bridges and orchestrates some functions in ``cemento.draw_io`` to do so.
#. ``cemento.term_matching``
        This module contains functions related to term matching and substitution, such as prefixes, namespace mappings, and fuzzy search.

Each module is again subdivided into different submodules that envelope functions based on their purpose:

* **preprocessing** - contains functions that deal with cleaning and organizing terms prior to use in other functions.
* **transforms** - deals with data transformations, aggregations and splitting for both final and intermediate data.
* **filters** - some functions that filter data that ended up being reused across modules.
* **io** - handles file or data loading from file or library sources.
* **constants** - contains fixed constants and definitions for dataclasses and enums.

As you can imagine, these combinations can help navigate the function you probably want to inspect. For example, you can bet that ``cemento.draw_io.io`` and ``cemento.draw_io.transforms`` will contain the functions for actually reading and writing a draw.io diagram.

The API guide
--------------

We invite you to read through our :doc:`API guide </modules>` to get an in-depth understanding of what each of the functions do. This codebase is more than 2,000 lines, and is still in active development. We cannot guarantee that all functions will have documentation, but we will slowly add as many of them as possible starting with the major functions for conversion.