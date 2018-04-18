"""client"""

# Imports
import socket
import sys
from config import client_config
from Packet import Packet

# Constants
CONFIG_FILE = "inputs/client.in"
PACKET_LEN = 50

# CMD Line Arguments
if len(sys.argv) > 2:
  raise Exception('Usage: client.py input_file.in')
elif len(sys.argv) == 2:
  CONFIG_FILE = sys.argv[1]

# More Constants
SERVER_IP, SERVER_PORT, CLIENT_PORT, FILE, RCV_WINDOW_SIZE = client_config(
    CONFIG_FILE)


MSG = FILE
SPLIT_MSG = [MSG[i:i+PACKET_LEN] for i in range(0, len(MSG), PACKET_LEN)]

# Creating client socket
S_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_CLIENT.bind(('localhost', CLIENT_PORT))

# Sending Packets
for i, msg in enumerate(SPLIT_MSG):
  packet = Packet(check_sum=1, seq_num=i, data=msg)
  S_CLIENT.sendto(packet.bytes(), (SERVER_IP, SERVER_PORT))
  print("Sent:", packet.bytes())

