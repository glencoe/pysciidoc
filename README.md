## pysciidoc

`pysciidoc` reads python docstrings and converts them to formatted asciidoc.
It is meant to be used in conjunction with [antora](https://antora.org/) to
automatically generate the documentation for the python package's API.

Find full documentation at https://glencoe.github.io/pysciidoc/

### Features

* automatically generate `nav.adoc` file for antora
* show type hints in documentation
* show default values for function arguments

### Installation

```bash
pip install 'git+https://github.com/glencoe/pysciidoc.git'
```

### Usage

```bash
pysciidoc --api-output-dir <path> --nav-file <path> <package-name>
```

#### Example using pysciidoc with antora to generate pysciidoc's API documentation
```bash
pysciidoc --api-output-dir docs/modules/api/pages \
  --nav-file docs/modules/api/nav.adoc pysciidoc
```

### Todo

- automatically format and link google doc style
  - [ ] examples
  - [ ] attributes
  - [ ] return values
- [ ] resolve type hints for `<factory>` from dataclass signatures


### Not planned
- support for annotated attributes and variables
  - not supported because there is no PEP specifying how to annotate these
