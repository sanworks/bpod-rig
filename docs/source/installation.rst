=====================
bpod-rig Installation
=====================

############
Requirements
############

``bpod-rig`` requires **Python 3.10 or later**. It is supported on Linux, macOS, and Windows.

See *pyproject.toml* for specific packages required by ``bpod-rig``


###########################
bpod Installation Directory
###########################

Before beginning, create a folder to serve as the **bpod Installation Directory**. This will serve as the location
for the :ref:`installation:Virtual Environment`, system configuration files, and anything else you want or need for your bpod
installation!

We will refer to the **bpod Installation Directory** as the ``BID``


###################
Virtual Environment
###################

``bpod-rig`` is designed to be installed and run within an isolated Python virtual environment. This allows a single machine
to have as many ``bpod-rig`` installations as needed or desired! There are many ways to create and manage virtual
environments. We recommend `Astral's uv <astral_uv_link_>`_ for virtual environment creation and management.

.. _astral_uv_link: https://docs.astral.sh/uv/

.. important:: The use of a virtual environment is not required, but is **highly** recommended.

..  attention:: At this time, we will not be explicitly supporting the use of conda/miniconda/Anaconda. Technically,
    it should still work, but use it at your own risk!

Creation
--------

Navigate to your **bpod Installation Directory (BID)** and run the following:

.. code-block:: console

    $ uv venv bpod-rig --python 3.14

Installing bpod-rig
-------------------

To install ``bpod-rig`` and its dependencies:

.. code-block:: console

    $ uv pip install bpod-rig

#################
Test Installation
#################

WIP

###############
Troubleshooting
###############

I can't connect to a Bpod on Linux
----------------------------------
If you're experiencing "Permission denied" errors, slow or unreliable connections,
missing data, or timeout errors when trying to connect to your Bpod on Linux, you likely
need to install additional udev rules.

By default, Linux restricts access to USB serial devices to root and members of the
``dialout`` group for security reasons. Additionally, system services like
`ModemManager <https://modemmanager.org/>`__  automatically probe serial devices to
detect modems, which can interfere with normal communication. Bpod devices use
`Teensy microcontrollers <https://www.pjrc.com/teensy/>`__, which appear as USB serial
devices that are subject to these restrictions.

Installing the `Teensy udev rules <https://www.pjrc.com/teensy/00-teensy.rules>`__
should solve these issues by:

- Granting all users read/write access to Teensy devices without requiring ``dialout``
  group membership
- Preventing `ModemManager <https://modemmanager.org/>`__  from probing and interfering
  with the connection
- Configuring serial ports with appropriate low-level settings (raw mode, no echo)
