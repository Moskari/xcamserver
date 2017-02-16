'''
Created on 11.1.2017

@author: sapejura
'''
import sys
import socket


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


def main(argv):
    receive_data((argv[1], int(argv[2])))


if __name__ == '__main__':
    main(sys.argv)
