Server module documentation
===========================

Messenger's server app.
Passes messages between the clients, handles user registration and authorization processes, stores users' public keys for encryption.

Usage:

``python server.py [-a {listen_address}] [-p {server_port}] [--no-gui]``

1. **-a** - sets a listen address for the server.
2. **-p** - sets a listen port for the server.
3. **--no-gui** - starts the server without a GUI (type /exit to close).

Examples:

``python server.py -a localhost``
 *Server will only listen for connections from "localhost"*

``python server.py -p 7777 --no-gui``
 *Launch the server without a GUI and make it listen on port 7777*

server.py
~~~~~~~~~

Main server app launcher module, contains a CLI arguments parser and an initialization script for network module and GUI window.

server.**arg_parser**()
    CLI parameters parser.
    Returns a tuple of

    * address
    * port (validated)
    * flag for launching without a GUI

add_user.py
~~~~~~~~~~~

.. automodule:: server.add_user
    :members:

config_window.py
~~~~~~~~~~~~~~~~

.. automodule:: server.config_window
    :members:

core.py
~~~~~~~

.. automodule:: server.core
    :members:

history_window.py
~~~~~~~~~~~~~~~~~

.. automodule:: server.history_window
    :members:

main_window.py
~~~~~~~~~~~~~~

.. automodule:: server.main_window
    :members:

remove_user.py
~~~~~~~~~~~~~~

.. automodule:: server.remove_user
    :members:

server_database.py
~~~~~~~~~~~~~~~~~~

.. automodule:: server.server_database
    :members:
