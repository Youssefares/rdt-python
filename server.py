"""server"""

# Imports
import socket
import sys
from config import server_config
from Packet import Packet
from multiprocessing import Process

# Constants
CONFIG_FILE = "inputs/server.in"
PACKET_LEN = 50

# CMD args
if len(sys.argv) > 2:
  raise Exception('Usage: server.py input_file.in')
elif len(sys.argv) == 2:
  CONFIG_FILE = sys.argv[1]

# More constants
SERVER_PORT, SND_WINDOW_SIZE, RND_SEED, LOSS_PROP = server_config(CONFIG_FILE)

# Creating server socket
S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_SERVER.bind(('localhost', SERVER_PORT))


def send_file(file_name, addr):
  """sends file content for file with specified file_name to client"""
  msg = open(file_name).read()
  split_msg = [msg[i:i+PACKET_LEN] for i in range(0, len(msg), PACKET_LEN)]
  # Sending Packets
  for i, msg in enumerate(split_msg):
    packet = Packet(check_sum=1, seq_num=i, data=msg)
    S_SERVER.sendto(packet.bytes(), addr)
    print("Replied with packet #%i:" % i, packet.bytes(), "To client: ", addr)


while True:
  PACKET, ADDR = S_SERVER.recvfrom(512) #Buffer_size = 512
  FILE_NAME = PACKET[3:].decode('utf-8')
  print("Filename requested by client: ", FILE_NAME, "Addr: ", ADDR)
  P = Process(target=send_file, args=[FILE_NAME, ADDR])
  P.start()
  P.join()