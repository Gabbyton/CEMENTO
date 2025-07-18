# SDLE FAIR Package: Centralized Entity Mapping & Extraction Nexus for Triples and Ontologies (CEMENTO)

**Description:**

This package is part of the larger SDLE FAIR application suite that features tools to create scientific ontologies faster and more efficiently. This package provides functional interfaces for converting draw.io diagrams of ontologies into RDF triples in the turtle (`.ttl`) format and vice versa. This package is able to provide term matching between reference ontology files and terms used in draw.io diagrams allowing for faster ontology deployment while maintaining robust cross-references for terms imported from other ontologies.

## Features

To summarize, the package offers the following features:
1. Converting RDF triples in `.ttl` files into draw.io diagrams of the ontology terms and relationships and vice versa
2. Converting `.ttl` files and/or draw.io diagrams of ontologies into an intermediate `networkx` graph format and vice versa (given proper formatting of course)
3. Substituting and matching terms based on ontologies that YOU provide
4. Creating coherent tree-based layouts for terms for visualizing ontology class and instance relationships
5. Tree-splitting diagram layouts to suppport multi-inheritance between classes (not recommended by BFO)
6. Support for URI prefixes (via binding) and literal annotations (language annotations like `@en` and datatype annotations like `^^xsd:string`)
7. Domain and range collection as a union for custom object properties.


## Installation

To install this particular package, use pip to install the latest version of the package:

```{bash}
pip install cemento
```

## Usage

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
If you have any questions or need further assistance, feel free to contact us at:

Email: 
[gop2@case.edu](Gabriel Obsequio Ponon)