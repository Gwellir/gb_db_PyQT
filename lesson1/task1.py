"""
Задача 1.

Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом
соответствующего сообщения («Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

from subprocess import Popen, PIPE
from ipaddress import ip_address


def host_is_available(address):
    """Test host availability by running 'ping' command."""
    try:
        address = ip_address(address)
    except ValueError:
        pass
    args = ['ping', str(address)]
    request_process = Popen(args, stdout=PIPE, stderr=PIPE)

    return_code = request_process.wait()

    return True if not return_code else False


def host_ping(address_list):
    """Check addresses in address list and show corresponding messages for each."""
    for address in address_list:
        if host_is_available(address):
            print(f'"{address}": узел доступен')
        else:
            print(f'"{address}": узел недоступен')


host_ping(['localhost', '10.10.10.10', '192.168.1.0', 'yandex.ru', '84.201.155.227', '99'])
