from GoBackN.GoBackNClient import GoBackNClient
import logging
import sys

if __name__ == '__main__':
    port_num = int(sys.argv[1])
    dest = sys.argv[2]

    logging.basicConfig(level=logging.DEBUG)
    GoBackNClient(('localhost', port_num)).request_file(('localhost', 6222), 'public/big_file.txt', dest)
    # GoBackNClient(('localhost', 5858)).request_file(('localhost', 6222), 'public/big_file.txt', 'c2.txt')