# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Guide]

- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.

_[Unreleased]_ section for tracking changes prior to binning to versions.

_[X.X.X] - YYYY-MM-YY_ for version-date header

## [0.9.4] - 2025-08-05

### Added

- dynamic version number detection in CLI message

## [0.9.3] - 2025-08-05

### Added

- center coordinates to `Connector` dataclass
- coordinate centering when rendering arrow positions (hasn't fixed stray arrows)

### Fixed

- horizontal offsets not switching in `draw_tree`
- non-rank stratified predicates being rendered as rank terms

## [0.9.2] - 2025-08-04

### Fixed

- `read_diagram` and `convert_graph_to_ttl` not running when using scripts
- null safety for folder variables. Get the default if not specified instead
- `convert_ttl_to_graph` with improper null behavior for folders
- example scripts in the example folder

## [0.9.1] - 2025-08-01

### Added

- contributor

### Fixed

- `assign_literal_ids` zips with uneven lengths

## [0.9.0] - 2025-08-01

### Added

- instance conformation for T-box and A-box separation for each tree
- draw divider line to demarcate instance conformation for T-box and A-box separation
- tree conformation to align all demarcation lines
- T-box and A-box labels
- box demarcation option to CLI
- divider line template xml file
- option for activating domain-range instance collection. Default behavior now is not to collect.

### Changed

- separated `draw_diagram` from `draw_tree` for future layout schemes

### Fixed

- `get_aliases` "eating up" the label if more alt labels are provided
- `get_severed_connectors` with a dangling function argument
- severed links not being added to the graph
- severed links being in reverse when displayed on the graph
- `convert_drawio_to_ttl` null safety for reference folder arguments

## [0.8.9] - 2025-07-25

### Added

- FAQs page for common issues and solutions
- section for citations and license in about page

### Changed

- adjusted `write_diagram` graph flipping for repaired orientations
- updated default arrow position calculation on `Connector` dataclass to reflect repaired orientations
- repository location. The CEMENTO repository is now "owned" by the CWRU-SDLE organization
- base URL for documentation. It is now in [https://cwru-sdle.github.io/CEMENTO/](https://cwru-sdle.github.io/CEMENTO/)

### Fixed

- term location not printing on diagram error causing error
- reversed arrow configuration on `connector.xml` template
- missing parent content for `missingChildError`

## [0.8.8] - 2025-07-25

### Added

- Shape type implementation for generating shapes
- New enum `ShapeType` for determining shape type

## [0.8.7] - 2025-07-24

### Added

- added new template files for class, instance, and literal
- more detailed key error message for `generate_graph`
- null safety checks after diagram error detection in `diagram_terms_iter`
- connected term location and ID when outputting diagram errors
- checks to ignore horizontal lines for diagram error checking

### Changed

- error check to make changes are made in-place if the user is already working n a file with "error_check" on the file name
- default terms in `drawio_to_ttl` to use all default terms in rdflib and in default file folders
- print out triples that passed diagram checks but caught in null check in `convert_graph_to_ttl`
- replaced all ghost connectors with straight orthogonal connectors

### Fixed

- fixed class and instance designation in graph_to_tll
- fixed error message input parsing

### Removed

removed root IDs from extracted terms and relationships in extract_elements

## [0.8.6] - 2025-07-24

### Added

- error check option on CLI
- term content in diagram error message
- defaults folder file contents to search terms
- feature to remove redundant statements about default namespace terms
- ability to define object properties
- support for multipage inputs
- feature to replace default object-property assignment to custom properties to swap with definitions if available

### Changed

- domain-range `.ttl` output to single element if only one
- to check errors by default
- updated examples for the new version
- updated figure with the new features

## [0.8.5] - 2025-07-23

### Added

- package documentation on github pages
- parse containers function
- googe site verification
- site logo and icon attribution
- sitemap
- reference ontology retrieval
- term types for all predicates
- restored error check feature on diagram, including error classes

### Changed

- hand-made XSD reference to XSD namespace inside `rdflib`
- no unique literals option to store true flag, setting no unique literals as the default behavior
- `file_path` argument in `conver_drawio_ttl` function to `input_path`

### Removed

- hand-made XSD reference
- do not check option
- not literal IDs

### Fixed

- exact match functionality not outputting all desired properties (label and SKOS exact match)
- non-bunny-eared data type string output
- prefixes not being imported from file

## [0.8.4] - 2025-07-20

**NOTE:** The changes listed here are a catch-all between this version and all prior releases. We haven't kept a good changelog until today, so we apologize for the broad statements to keep this document section brief.

### Added

- application CLI
- support for converting directly to `.ttl` files from draw.io and vice versa
- support for literals and literal annotations (language and datatype)
- term matching via reference ontologies
- ability to add reference ontologies
- unique literal ID generation option
- support for annotation types
- classes-only option for drawing layouts
- ability to write prefixes
- tree-splitting for dealing with multiple inheritance
- stratified term category (includes definitions, annotations, etc.) for prioritizing in the layout
- match suppression with star keys
- alias support with parenthetic notation
- README instructions on CLI and scripting for new package implementation

### Changed

- programmming paradigm, from an clunky OOP-based approach to a hybrid functional approach
- File structure, adopting file conventions in functional programming
- all prior functionality implementations except those expressly mentioned in the remove section
- choosing more general category of terms to draw in the tree layout (stratified) versus just rank terms (subclass and type)
- shape definitions from native classes to dataclasses
- rendering shapes directly from dataclasses instead of through manual prop generation
- computing arrow directions dynamically based on shape angle instead of static case-based matching
- example scripts

### Removed

- All functions built under the OOP-based software
- shape-extent-based area diagram reading
- circle-based (organic) layouts
- straight-arrow and curve template files
- error detection in diagram reads
- defer-layout option
