# SDLE FAIR Package: Centralized Entity Mapping & Extraction Nexus for Triples and Ontologies (CEMENTO)

**Description:**

This package is part of the larger SDLE FAIR application suite that features tools to create scientific ontologies faster and more efficiently. This package provides functional interfaces for converting draw.io diagrams of ontologies into RDF triples in the turtle (`.ttl`) format and vice versa. This package is able to provide term matching between reference ontology files and terms used in draw.io diagrams allowing for faster ontology deployment while maintaining robust cross-references for terms imported from other ontologies.

## Features

To summarize, the package offers the following features:

1. Converting RDF triples in `.ttl` files into draw.io diagrams of the ontology terms and relationships and vice versa
2. Converting `.ttl` files and/or draw.io diagrams of ontologies into an intermediate `networkx` graph format and vice versa (given proper formatting of course)
3. Substituting and matching terms based on ontologies that YOU provide
4. Creating coherent tree-based layouts for terms for visualizing ontology class and instance relationships
5. Tree-splitting diagram layouts to suppport multi-inheritance between classes (though multiple inheritance is not recommended by BFO)
6. Support for URI prefixes (via binding) and literal annotations (language annotations like `@en` and datatype annotations like `^^xsd:string`)
7. Domain and range collection as a union for custom object properties.

## Installation

To install this particular package, use pip to install the latest version of the package:

```{bash}
pip install cemento
```

## Usage

The package only currently supports a python script interface for using the functions. The following sections can show how to use the package for the its most common (and simplest) use-cases:

### Converting draw.io to `.ttl` files

Four paths are required to fully utilize all CEMENTO features for this purpose. `INPUT_PATH` and `OUTPUT` are your input draw.io and output `.ttl` file paths, respectively.

`ONTO_PATH` points to a folder containing `.ttl` files that contain the terms you want to reference. For example, you can download the `cco.ttl` from the official [CCO repo page](https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/develop/src/cco-merged/CommonCoreOntologiesMerged.ttl) and place it here to reference all cco terms. Under the hood, this referencing is additive, which means you can add as many `.ttl` as you want to reference.

**CAUTION:** Repeated references are overwritten in the order the files are read by python (usually alphabetical order). If your reference files conflict with one another, please be advised and resolve those conflicts first by deleting the terms or modifying them.

Using the actual function is as easy as importing and calling it in a python script.

```{python}
from cemento.rdf.drawio_to_turtle import convert_drawio_to_ttl

INPUT_PATH = "your_onto_diagram.drawio"
OUTPUT_PATH = "your_triples.ttl"
ONTO_PATH = "data" # this path points to the folder containing all the ttl files you want to reference (optional)
DEFAULTS_FOLDER = "" # path to the folder containing default terms. It should come with the cloned repo (optional)
PREFIXES_PATH = "prefixes.json" # this path points to a prefixes file with custom prefix assignments (optional)

if __name__ == "__main__":
    convert_drawio_to_ttl(INPUT_PATH, OUTPUT_PATH, ONTO_PATH, PREFIXES_PATH)
```

### Converting `.ttl` files to draw.io files

This case is very similiar to the previous one. The `.ttl` was assumed to contain the necessary information so you only need to set the `INPUT_PATH` and `OUTPUT_PATH`.

```{python}
from cemento.rdf.turtle_to_drawio import convert_ttl_to_drawio

INPUT_PATH = "your_triples.ttl"
OUTPUT_PATH = "your_onto_diagram.drawio"

if __name__ == "__main__":
    # the horizontal tree parameter controls whether you want the default vertical tree (False) or an inverted horizontal tree (True)
    convert_ttl_to_drawio(INPUT_PATH, OUTPUT_PATH, horizontal_tree=False)
```

## Converting draw.io to a `networkx` DiGraph

We used a directed `networkx` graph (DiGraph) as an intermediary data structure that provides a much richer interface for graph manipulation than the default `rdflib` Graph. If you are interested in using this data structure, you are free to use the functions shown below:

```{python}
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
```

In fact, the functions `read_drawio` and `convert_ttl_to_graph` are actually wrapped around to form the `convert_ttl_to_drawio` and `convert_drawio_to_ttl` functions. You are already using the former pair when using the latter.

### Important Note

When using the `read_drawio`, please exercise caution when providing the paths. The function has a signature:
```{python}
read_drawio( input_path: str | Path, onto_ref_folder: str | Path = None, prefixes_folder: str | Path = None, defaults_folder: str | Path = None, relabel_key: DiagramKey = DiagramKey.LABEL, inverted_rank_arrow: bool = False)
```
If you aren't planning on leveraging stratified layouts like the ones used in `draw_tree`, please supply just the arguments for `input_path` and optionally, `relabel_key` and `inverted_rank_arrow`.

## Drawing Basics

pending

## Future Features

This package was designed with end-to-end conversion in mind. The package is still in active development, and future features may include, but are not limited to the following:

- **Providing substitution lists.** The package will also be able to provide a list of substituted terms.
- **Suppressing substitutions.** The package will be able to take a special symbol to suppress substitutions for when your custom term is a little bit too close to an existing term.
- **Object Property definitions.** A future version of this package will be able to support object property definitions.
- **Multi-page diagrams.** The package parses terms with the same name as being the same entity. The package will be able to support multiple pages for when you want to organize terms your way.
- **An interactive mode.** Users will be able to visualize syntax errors, improper term connections (leveraging domains and ranges), and substitutions and make edits in iterations before finalizing a draw.io or `.ttl` output.
- **Comprehensive domain-range inference.** The package will not only be able to collect unions of terms, but infer them based on superclass term definitions.
- **Integrated reasoner.** Packages like `owlready2` have reasoners like `HermiT` and `Pellet` that will be integrated to diagram-to-triple conversion. This is for when some implicit connections that you would want to make are a little bit tedious to draw but are equally as important.

## License

This project was released under the BSD-3-Clause License. For more information about the license and the Open Source movement, please check the [Open Source Initiative](https://opensource.org/licenses) website.

## Contact Information

If you have any questions or need further assistance, please open a GitHub issue we can assist you there.
