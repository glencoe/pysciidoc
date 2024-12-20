# pysciidoc

# Getting started with this template

If you want to use the workflows to publish packages to pypi/testpypi you first need to upload a package
for this project to each of these registries once.
This step will initially create the corresponding projects (ci pipeline is not allowed to do that).
And you need to create a trusted publisher with the following values:

 - for pypi: `environment = pypi`, `workflow file = publish.yml`
 - for testpypi: `environment = testpypi`, `workflow file = publish_test.yml` 

## Installation


## Usage
