'''
Created on 15.12.2016

@author: sapejura
'''
import socket
# from xevacam import utils
import requests


def init(addr):
    print('INIT')
    r = requests.post(addr + "/init", timeout=5)
    print(r.status_code, r.reason)
    print(r.text)
    resp = r.json()
    if resp['status'] != 'STOPPED':
        print('status is not STOPPED, it\'s %s' % resp['status'])
        return


def start(addr):
    print('START')
    r = requests.post(addr + "/start", timeout=5)
    print(r.status_code, r.reason)
    print(r.text)
    if r.status_code is 200 and r.reason == 'OK':
        return r.json()
    else:
        return None


def receive_data(addr_tuple):
    print('CONNECTING TO SOCKET %s:%s' % tuple(addr_tuple))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(tuple(addr_tuple))
    cs = client_socket.makefile(mode='rb')

    print('CONNECTED')
    try:
        # Make a file-like object out of the connection
        # connection = client_socket.makefile('rb')
        # input('Enter')
        i = 0
        while True:
            # data = connection.read(163840)
            # data = client_socket.recv(1024)
            data = cs.read(163840)
            if data != b'':
                # print(data)
                print('Got', len(data), 'bytes frame data,', i)
                # print('Got', len(data), 'bytes frame data,', i)
                i += 1
            else:
                print('No frame data')
            # print(connection.read(163840))
            # a = input('asdasd>')
            # if a != '':
            #    break
    except:
        raise
    finally:
        print('Closing connection...')
        # connection.close()
        client_socket.close()
        print('...closed.')


def main():
    print('Starting')
    addr = "http://127.0.0.1:5000"
    init(addr)
    input('Enter')
    resp = start(addr)
    socket_addr = resp['stream_address']
    if socket_addr is None:
        print('Received data didn\'t have socket address')
        return
    receive_data(socket_addr)


if __name__ == '__main__':
    main()
