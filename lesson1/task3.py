"""
Задача 3.

Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate).
"""

from subprocess import Popen, PIPE
from ipaddress import ip_interface
from tabulate import tabulate


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


def host_range_ping_tab(first_address, last_address):
    """Check addresses in address range and generate a summary table."""
    address_list = generate_ip_list(first_address, last_address)
    if not address_list:
        print('Given addresses do not belong to the same network range or are invalid.')
        return
    print(f'Testing ips: {[str(address) for address in address_list]}')
    reachable = []
    unreachable = []
    for address in address_list:
        if host_is_available(address):
            reachable.append(address)
            print('.', end='')
        else:
            unreachable.append(address)
            print('x', end='')
    print('\n')
    table = [('Reachable', 'Unreachable')]
    for i in range(max(len(reachable), len(unreachable))):
        table.append((reachable[i] if i < len(reachable) else '',
                     unreachable[i] if i < len(unreachable) else ''))
    print(tabulate(table, headers='firstrow', tablefmt='pipe'))


host_range_ping_tab('84.201.155.227', '84.201.155.231')
