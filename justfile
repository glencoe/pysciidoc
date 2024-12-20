test_run:
  #!/usr/bin/env bash
  if [ -d test_doc ]; then
    rm -r test_doc
  fi
  mkdir test_doc
  uv run pysciidoc -o test_doc pysciidoc
  cd test_doc
  asciidoctor -a sectanchors=true -a sectlinks=true -a source-highlighter=rouge *.adoc
  cd ..
