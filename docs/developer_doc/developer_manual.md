# Development

## Generate the documentation
This requires:
- [Sphinx](https://www.sphinx-doc.org/en/master/)
```bash
pip3 install -r developer-requirements.txt
```

Build the doc as following (From within the repository root dir)
```bash
cd docs
make html
```

push the doc as following (From within the repository root dir)
```bash
cd docs
make push-docs
```

The build documentation will be available in the folder `docs/sphinx/_build/html`.

## Package Project

