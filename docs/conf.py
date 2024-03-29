# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

CONF_MUTERIA_TOP_DIR = os.path.dirname(os.path.abspath('.'))
CONF_MUTERIA_PKG = "muteria"

sys.path.insert(0, CONF_MUTERIA_TOP_DIR)
#sys.path.insert(0, os.path.join(CONF_MUTERIA_TOP_DIR, CONF_MUTERIA_PKG))


# -- Project information -----------------------------------------------------

project = 'Muteria'
copyright = '2022, Thierry TITCHEU CHEKAM'
author = 'Thierry TITCHEU CHEKAM'

# The full version, including alpha/beta/rc tags
import muteria
release = muteria.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinxcontrib.apidoc',
    'myst_parser',
]

autosummary_generate = True  # Turn on sphinx.ext.autosummary
apidoc_module_dir = os.path.join(CONF_MUTERIA_TOP_DIR, CONF_MUTERIA_PKG) # sphinxcontrib.apidoc config
apidoc_output_dir = os.path.join('sphinx', '_reference') # sphinxcontrib.apidoc config
apidoc_separate_modules = True # sphinxcontrib.apidoc config

# Add any paths that contain templates here, relative to this directory.
templates_path = [os.path.join('sphinx', '_templates')]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
        os.path.join('sphinx', '_build'), 
        os.path.join('sphinx', 'Thumbs.db'), 
        os.path.join('sphinx', '.DS_Store')
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'bizstyle'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = [os.path.join('sphinx', '_static')]

html_context = {
    'github_user_name': 'muteria', 
    'github_repo_name': 'muteria',
    'project_name': 'Muteria'
}

source_suffix = ['.rst', '.md']
