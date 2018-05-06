from GoBackN.GoBackNClient import GoBackNClient
from SelectiveRepeat.SelectiveRepeatClient import SelectiveRepeatClient

import logging
import sys

client_class_dict = {
  'gbn': GoBackNClient,
  'sr': SelectiveRepeatClient
}

if __name__ == '__main__':
    client_protocol = sys.argv[1]
    port_num = int(sys.argv[2])
    dest = sys.argv[3]

    # get class constructor from first cmd line arg
    client = client_class_dict[client_protocol]

    logging.basicConfig(level=logging.DEBUG)
    client(('localhost', port_num)).request_file(('localhost', 6222), 'public/small_file.txt', dest)
