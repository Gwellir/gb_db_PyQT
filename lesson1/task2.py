"""
Задача 2.

Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""

from subprocess import Popen, PIPE
from ipaddress import ip_interface


def host_is_available(address):
    """Test host availability by running 'ping' command."""
    args = ['ping', str(address)]
    request_process = Popen(args, stdout=PIPE, stderr=PIPE)

    return_code = request_process.wait()

    return True if not return_code else False


def generate_ip_list(start, finish):
    """Return a range of IPV4Addresses based on start and finish values."""
    try:
        ip_start = ip_interface(f'{start}/24')
        ip_finish = ip_interface(f'{finish}/24')
        if ip_finish.network == ip_start.network:
            if ip_start.ip > ip_finish.ip:
                ip_start, ip_finish = ip_finish, ip_start
            address_list = []
            ip_current = ip_start
            while ip_current.ip <= ip_finish.ip:
                address_list.append(ip_current.ip)
                ip_current += 1
            return address_list
        return None
    except ValueError:
        return None


def host_range_ping(first_address, last_address):
    """Check addresses in address range and show corresponding messages for each."""
    address_list = generate_ip_list(first_address, last_address)
    if not address_list:
        print('Given addresses do not belong to the same network range or are invalid.')
        return
    print(f'Testing ips: {[str(address) for address in address_list]}')
    for address in address_list:
        if host_is_available(address):
            print(f'"{address}": узел доступен')
        else:
            print(f'"{address}": узел недоступен')


host_range_ping('84.201.155.227', '84.201.155.230')
