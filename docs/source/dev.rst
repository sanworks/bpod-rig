=================
Development Setup
=================

Here you can find the recommended developemnt setup. The ``bpod-rig`` repository is shipped as a JetBrains PyCharm project.


Install UV
**********

``bpod-rig`` utilizes uv as its environment and development tools manager

Install `uv` using one of the methods described here: https://github.com/astral-sh/uv


Clone Repository
****************

1. Clone the repository using the following command:

.. code-block:: shell-session

    $ git clone https://github.com/sanworks/bpod-rig

or

.. code-block:: shell-session

    $ git clone git@github.com:sanworks/bpod-rig

2. Move into the cloned repository
3. Checkout the dev branch

.. code-block:: shell-session

    $ git checkout dev


Create Virtual Environment
**************************

1. Navigate into the cloned respository
2. Run the following command to create a virtual environment with all development dependencies

.. code-block:: shell-session

    $ uv sync --extra dev

3. (Optional) If it is desired to install the dependencies for building the documentation, use the following command instead

.. code-block:: shell-session

    $ uv sync --extra dev --extra docs

or

.. code-block:: shell-session

    $ uv sync --all-extras


Once complete there will be a new *.venv* folder containing an isolated Python installation and the desired dependencies
