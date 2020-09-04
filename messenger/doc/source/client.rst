Client module documentation
======================================

This is a client-side application for the messenger. Used to send messages to other online clients, store and display message history and contact lists.
Uses RSA encryption with 2048-bit keys.

May use the following CLI arguments:

``python client.py {server host} {server port} -n {username} -p {password}``

Examples:

* ``python client.py ip_address port_number``

 *Client will try to connect to the server on ip_address:port_number*


* ``python client.py ip_address port_number -n test1 -p 123456``

 *Client will try to connect to the server on ip_address:port_number using a username of "test1" and password "123456"*

client.py
~~~~~~~~~

A launcher script of the client app, contains a CLI argument parser and an initialization method for network transport and GUI.

client. **arg_parser** ()
    CLI parameters parser.
    Returns a tuple of

    * address
    * port (validated)
    * username
    * password for user

add_contact.py
~~~~~~~~~~~~~~

.. automodule:: client.add_contact
    :members:

client_database.py
~~~~~~~~~~~~~~~~~~

.. automodule:: client.client_database
    :members:

client_gui_designer.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: client.client_gui_designer
    :members:

del_contact.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: client.del_contact
    :members:

main_window.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: client.main_window
    :members:

start_dialog.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: client.start_dialog
    :members:

transport.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: client.transport
    :members:
