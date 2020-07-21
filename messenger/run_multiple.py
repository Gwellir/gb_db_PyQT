from subprocess import Popen, CREATE_NEW_CONSOLE
from time import sleep

p_list = []
amount = 2

while True:
    user = input(f'Launch the server and N clients (default: {amount}) (s) / Close all (x) / Exit (q) ')

    if user == 'q':
        break
    elif user == 's':
        num = input(f'How many clients would you like ro run ({amount}): ')
        if num != '':
            try:
                amount = int(num)
            except ValueError:
                print('Please enter a valid number!')
                continue
        p_list.append(Popen(f'python server.py', creationflags=CREATE_NEW_CONSOLE))
        sleep(1)
        for i in range(amount):
            sleep(1 / amount)
            p_list.append(Popen(f'python client.py -a localhost -p 7777 -u user{i}', creationflags=CREATE_NEW_CONSOLE))
        print(f'launched {amount} clients')
    elif user == 'x':
        for p in p_list:
            p.kill()
        p_list.clear()