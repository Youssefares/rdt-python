import logging
import sys

from GoBackN.GoBackNClient import GoBackNClient
from SelectiveRepeat.SelectiveRepeatClient import SelectiveRepeatClient
from StopAndWaitClient import main_receive_loop
from config import client_config


# Constants
CONFIG_FILE = "inputs/client.in"

# More Constants
SERVER_IP, SERVER_PORT, CLIENT_PORT, FILE, RCV_WINDOW_SIZE = client_config(CONFIG_FILE)

client_class_dict = {
  'gbn': GoBackNClient,
  'sr': SelectiveRepeatClient
}

if __name__ == '__main__':
    client_protocol = sys.argv[1]
    dest = sys.argv[2]
    
    probability = 0.3
    seed_num = 3000
    if client_protocol == 'sw':
      main_receive_loop(file_name, probability, seed_num)
    else:
      # get class constructor from first cmd line arg
      client = client_class_dict[client_protocol]


      logging.basicConfig(level=logging.DEBUG)
      client(('localhost', CLIENT_PORT), probability, seed_num).request_file((SERVER_IP, SERVER_PORT), FILE, dest)
