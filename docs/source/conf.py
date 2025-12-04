from datetime import date
from importlib import metadata

BPOD_RIG_VERSION = metadata.version('bpod-rig')
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bpod-rig'
copyright = f'{date.today().year}, Sanworks'
author = 'Sanworks'
release = '.'.join(BPOD_RIG_VERSION.split('.')[:3])
version = '.'.join(BPOD_RIG_VERSION.split('.')[:3])
rst_prolog = f"""
.. |version_code| replace:: ``{version}``
"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_copybutton',
    'sphinx_autodoc_typehints',
    'sphinx-jsonschema',
]
source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = []

typehints_defaults = None
typehints_use_rtype = False
typehints_use_signature = False
typehints_use_signature_return = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.10/', None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
    'serial': ('https://pyserial.readthedocs.io/en/stable/', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    # 'display_version': True,
}

# # -- Settings for automatic API generation -----------------------------------
# autodoc_mock_imports = ['_typeshed']
# autodoc_class_signature = 'separated'  # 'mixed', 'separated'
# autodoc_member_order = 'groupwise'  # 'alphabetical', 'groupwise', 'bysource'
# autodoc_inherit_docstrings = False
# autodoc_typehints = 'description'  # 'description', 'signature', 'none', 'both'
# autodoc_typehints_description_target = 'all'  # 'all', 'documented', 'documented_params'
# autodoc_typehints_format = 'short'  # 'fully-qualified', 'short'
#
# autosummary_generate = True
# autosummary_imported_members = False
#
# napoleon_google_docstring = False
# napoleon_numpy_docstring = True
# napoleon_include_init_with_doc = False
# napoleon_include_private_with_doc = False
# napoleon_include_special_with_doc = False
# napoleon_use_admonition_for_examples = True
# napoleon_use_admonition_for_notes = True
# napoleon_use_admonition_for_references = True
# napoleon_use_ivar = True
# napoleon_use_param = True
# napoleon_use_rtype = True
# napoleon_use_keyword = True
# napoleon_preprocess_types = True
# napoleon_type_aliases = None
# napoleon_attr_annotations = True
