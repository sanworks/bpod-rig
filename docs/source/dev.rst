=================
Development Setup
=================

Here you can find the recommended development setup. The ``bpod-rig`` repository is shipped as a JetBrains PyCharm project.


Install UV
**********

``bpod-rig`` utilizes uv as its environment and development tools manager

Install `uv` using one of the methods described here: https://github.com/astral-sh/uv


Clone Repository
****************

1. Clone the repository using the following command:

.. code-block:: console

    $ git clone https://github.com/sanworks/bpod-rig

or if you have ssh setup

.. code-block:: console

    $ git clone git@github.com:sanworks/bpod-rig

2. Move into the cloned repository
3. Checkout the dev branch

.. code-block:: console

    $ git checkout dev

4. Create and checkout a feature branch

    $ git checkout -b [FEATURE BRANCH NAME]

.. code-block:: console

Create Virtual Environment
**************************

1. Navigate into the cloned repository
2. Run the following command to create a virtual environment with all development dependencies

.. code-block:: console

    $ uv sync --group dev

3. (Optional) If it is desired to install the dependencies for building the documentation, use the following command instead

.. code-block:: console

    $ uv sync --group dev --group docs

or

.. code-block:: console

    $ uv sync --all-groups


Once complete there will be a new *.venv* folder containing an isolated Python installation and the desired dependencies

Open PyCharm Project
********************

1. Start PyCharm and open the `bpod-rig` directory as a project
2. Add the newly created .venv as the project interpreter
    See `Link here <https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html>` for more information
3. Start Developing!
