# SDLE FAIR Package: Centralized Entity Mapping & Extraction Nexus for Triples and Ontologies (CEMENTO)

**Description:**

This package is part of the larger SDLE FAIR application suite that features tools to create scientific ontologies faster and more efficiently. This package provides functional interfaces for converting draw.io diagrams of ontologies into RDF triples in the turtle (`.ttl`) format and vice versa. This package is able to provide term matching between reference ontology files and terms used in draw.io diagrams allowing for faster ontology deployment while maintaining robust cross-references.

## Features

To summarize, the package offers the following features:

1. Converting RDF triples in `.ttl` files into draw.io diagrams of the ontology terms and relationships and vice versa
2. Converting `.ttl` files and/or draw.io diagrams of ontologies into an intermediate `networkx` graph format and vice versa (given proper formatting of course)
3. Substituting and matching terms based on ontologies that YOU provide
4. Creating coherent tree-based layouts for terms for visualizing ontology class and instance relationships
5. Tree-splitting diagram layouts to suppport multiple inheritance between classes (though multiple inheritance is not recommended by BFO)
6. Support for URI prefixes (via binding) and literal annotations (language annotations like `@en` and datatype annotations like `^^xsd:string`)
7. Domain and range collection as a union for custom object properties.
8. Providing a log for substitutions made and suppresing substitutions by adding a key (\*).
9. Support for Property definitions. Properties that do not have definitions will default as an Object Property type.
10. Support for multiple pages in a draw.io file, for when you want to organize terms your way.

## Installation

To install this particular package, use pip to install the latest version of the package:

```{bash}
pip install cemento
```

## Usage

### Command Line Interface

Once the package is installed, you will have access to a `cemento` CLI command for converting files. This CLI interface allows you to convert `.ttl` files into draw.io diagrams and vice versa. To do so:

```{bash}
# converting from .ttl to drawio
cemento ttl_drawio your_triples.ttl your_output_diagram.drawio
# converting from .drawio to .ttl
cemento drawio_ttl your_output_diagram.drawio your_triples.ttl
```

It is that simple. By default, the program compiles with the versions of the reference ontologies it needs to do term matching. Specifically, it comes bundled with the following ontologies.

- [Common Core Ontologies](https://github.com/CommonCoreOntology/CommonCoreOntologies)
- [OWL Schema](https://www.w3.org/2002/07/owl#)
- [RDF Schema](https://www.w3.org/1999/02/22-rdf-syntax-ns#)
- [RDFS Schema](https://www.w3.org/2000/01/rdf-schema#)

These ontology files are used by `CEMENTO` for referencing terms and predicates. As you can imagine, the default reference ontology is CCO, which is the preferred mid-level ontology by the SDLE center. The next section details how you can add your own reference ontologies.

The schemas for RDF, XML, and RDFS contain the terms that all ontologies ought to understand by default. Thus, a lot of assumptions were made surrounding their standard use during the development of the package. You can, however, also specify a folder of choice through the `--defaults-folder-path` option for `cemento ttl_drawio`.

#### Adding Reference Ontologies

The `cemento ttl_drawio` command has an argument called `--onto-ref-folder-path` which you can point to a folder containing `.ttl` files that contain the terms you want to reference. For example, you can download the `cco.ttl` from the official [CCO repo page](https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/develop/src/cco-merged/CommonCoreOntologiesMerged.ttl) and place it here to reference all cco terms. Under the hood, this referencing is additive, which means you can add as many `.ttl` as you want to reference. By default, `cemento` will already come bundled with this folder, but it will currently only reference CCO.

**CAUTION:** Repeated references are overwritten in the order the files are read by python (usually alphabetical order). If your reference files conflict with one another, please be advised and resolve those conflicts first by deleting the terms or modifying them.

#### Adding Custom Prefixes

Adding custom prefixes are crucial when creating your own terms and namespaces. **IMPORTANT:** `CEMENTO` will not be able to process your custom term and prefix if it does not know the IRI to which it points. The `CEMENTO` package comes bundled with a default set of prefixes it uses to parse prefixes used in drawio ontology diagrams.

To add a custom prefix, create a file that models the contents of `examples/prefixes.json`, which is included for your reference. In addition, please set the `--prefix-file-path` option in `cemento drawio_ttl` to use a custom folder that contains your prefix-namespace pairs. The package will defer to the default `default_prefixes.json` (which is identical in content but not the same as the one in `examples/prefixes.json`) unless this path is specified.

## Scripting

The package is composed of four main modules that can be imported into a python script. The following sections can show how to use the package for the its most common (and simplest) use-cases:

### Converting draw.io to `.ttl` files

Using the actual function is as easy as importing and calling it in a python script. The function takes the exact same arguments that you can set in `cemento drawio_ttl`. In this case, the script needs to set those arguments explicitly.

```{python}
from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl

INPUT_PATH = "happy-example.drawio"
OUTPUT_PATH = "sample.ttl"
LOG_PATH = ""

if __name__ == "__main__":
    convert_drawio_to_ttl(
        INPUT_PATH,
        OUTPUT_PATH,
        check_errors=True, # set whether to check for diagram errors prior to processing
        log_substitution_path=LOG_PATH, # set where to save the substitution log for term fuzzy search
        collect_domains_ranges=False, # set whether to collect the instances within the domain and range of a custom object property
    )
```

### Converting `.ttl` files to draw.io files

This case is very similiar to the previous one. The `.ttl` was assumed to contain the necessary information so you only need to set the `INPUT_PATH` and `OUTPUT_PATH`. The options `check_ttl_validity` and `set_unique_literals` set the default behavior of rule-checking the `ttl` file first, and treating literals with the same name as different things, respectively.

```{python}
from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

INPUT_PATH = "your_onto.ttl"
OUTPUT_PATH = "your_diagram.drawio"

if __name__ == "__main__":
    convert_ttl_to_drawio(
        INPUT_PATH,
        OUTPUT_PATH,
        horizontal_tree=False, #sets whether to display tree horizontally or vertically
        set_unique_literals=False, # sets whether to make literals with the same content, language and type unique
        classes_only=False, # sets whether to display classes only, useful for large turtles like CCO
        demarcate_boxes=True, # sets whether to move all instances to A-box and classes to T-box
    )
```

### Converting draw.io to a `networkx` DiGraph

We used a directed `networkx` graph (DiGraph) as an intermediary data structure that provides a much richer interface for graph manipulation than the default `rdflib` Graph. If you are interested in using this data structure, you are free to use the functions shown below:

```{python}
from cemento.draw_io.read_diagram import read_drawio
from cemento.draw_io.write_diagram import draw_tree

INPUT_PATH = "happy-example.drawio"
OUTPUT_PATH = "sample.drawio"

if __name__ == "__main__":
    # reads a drawio file and converts it to a networkx graph
    graph = read_drawio(
        INPUT_PATH,
        check_errors=True,
        inverted_rank_arrow=False # set whether the rdfs:subClassOf and rdf:type were inverted
    )
    # reads a networkx graph and draws a draw.io diagram
    draw_tree(
        graph,
        OUTPUT_PATH,
        translate_x=0,
        translate_y=0,
        classes_only=False,
        demarcate_boxes=True,
        horizontal_tree=False,
    )
```

In fact, the functions `read_drawio` and `convert_ttl_to_graph` are actually wrapped around to form the `convert_ttl_to_drawio` and `convert_drawio_to_ttl` functions. You are already using the former pair when using the latter.

### A Note on "Unique" Literals

By default, the package will treat all literals as being unique from one another. This is in contrast to terms which have singular, unique IRIs which are treated to be the same if drawn in multiple locations. To make unique literals (which don't come with IRIs), the package appends all literal terms with a unique ID that prevents merging. Thus, while working with DiGraphs, you will notice that the literals will come with a preprended ID.

You are free to remove them using `remove_literal_id` which is just one of the functions we wrote in `cemento.draw_io.preprocessing`. You are also free to implement your own algorithm as well.

## Drawing Basics

The following diagram goes through an example supplied with the repository called `happy-example.drawio` with its corresponding `.ttl` file called `happy-example.ttl`. We used [CCO terms](https://github.com/CommonCoreOntology/CommonCoreOntologies) to model the ontology, so please download that file and place it into your `ONTO_REF_FOLDER` so you can follow along.

![happy-exampl-explainer-diagram](figures/happy-example-explainer.drawio.svg)

**NOTE:** Click on the figure and click the `Raw` button on the subsequent page to enlarge. If you prefer, your can also refer to the `do-not-input-this-happy-example-explainer.drawio` file found in the `figures` folder.

## Future Features

This package was designed with end-to-end conversion in mind. The package is still in active development, and future features may include, but are not limited to the following:

- **Axioms and Restrictions.** Users will be able to draw out their axioms and restrictions, starting from basic domains and ranges, all the way to restrictions and onProperties.
- **An interactive mode.** Users will be able to visualize syntax errors, improper term connections (leveraging domains and ranges), and substitutions and make edits in iterations before finalizing a draw.io or `.ttl` output.
- **Comprehensive domain-range inference.** The package will not only be able to collect unions of terms, but infer them based on superclass term definitions.
- **Integrated reasoner.** Packages like `owlready2` have reasoners like `HermiT` and `Pellet` that will be integrated to diagram-to-triple conversion. This is for when some implicit connections that you would want to make are a little bit tedious to draw but are equally as important.

## License

This project was released under the BSD-3-Clause License. For more information about the license, please check the attached `LICENSE.md` file. For more about the Open Source movement, please check the [Open Source Initiative](https://opensource.org/licenses) website.

## Contact Information

If you have any questions or need further assistance, please open a GitHub issue and we can assist you there.
