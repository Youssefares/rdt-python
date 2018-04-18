"""server"""

import socket
import sys
from config import server_config

CONFIG_FILE = "inputs/server.in"
if len(sys.argv) > 2:
  raise Exception('Usage: server.py input_file.in')
elif len(sys.argv) == 2:
  CONFIG_FILE = sys.argv[1]

SERVER_PORT, SND_WINDOW_SIZE, RND_SEED, LOSS_PROP = server_config(CONFIG_FILE)

S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_SERVER.bind(('localhost', SERVER_PORT))

while True:
  file_name, addr = S_SERVER.recvfrom(512) #Buffer_size
  print("Message: ", file_name, "Addr: ", addr)
