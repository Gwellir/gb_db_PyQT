import dis


class ServerWatcher(type):
    """A Metaclass for checking Server class implementation."""

    def __init__(self, clsname, bases, clsdict):
        """Tests a Server class for not using client-side methods and initializing a socket correctly."""

        methods = set()
        attrs = set()
        socket_attrs = []

        # print(clsdict)
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                # print(clsdict[func], list(ret))
                lst_ret = list(ret)
                for i in range(len(lst_ret)):
                    # print(lst_ret[i])
                    if lst_ret[i].argval == 'socket':
                        j = 1
                        # looks up which constants follow "socket" initialization
                        # as I am not using "socket.attr" notation, they do not show up as "LOAD_ATTR"
                        # but are listed as "LOAD_GLOBAL" instead
                        while lst_ret[i+j].opname == 'LOAD_GLOBAL' and not lst_ret[i+j].starts_line:
                            socket_attrs.append(lst_ret[i+j].argval)
                            j += 1
                    if lst_ret[i].opname in ['LOAD_GLOBAL', 'LOAD_METHOD']:
                        methods.add(lst_ret[i].argval)
                    elif lst_ret[i].opname == 'LOAD_ATTR':
                        attrs.add(lst_ret[i].argval)
        # print(methods)
        # print(socket_attrs)
        if 'connect' in methods:
            raise TypeError('Cannot use "connect" method in server class.')
        if not ('SOCK_STREAM' in socket_attrs and 'AF_INET' in socket_attrs):
            raise TypeError('Wrong socket initialization parameters')
        super().__init__(clsname, bases, clsdict)