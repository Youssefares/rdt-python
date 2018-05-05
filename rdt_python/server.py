"""server"""

# Imports
import socket
import sys
import logging
from config import server_config
from Packet import Packet
from multiprocessing import Process
from DemuxHandler import DemuxHandler

# Constants
CONFIG_FILE = "inputs/server.in"
PACKET_LEN = 500

# CMD args
# if len(sys.argv) > 2:
#   raise Exception('Usage: server.py input_file.in')
# elif len(sys.argv) == 2:
#   CONFIG_FILE = sys.argv[2]

# Logger configs
logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

# More constants
SERVER_PORT, SND_WINDOW_SIZE, RND_SEED, LOSS_PROP = server_config(CONFIG_FILE)

# Creating server socket
S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_SERVER.bind(('localhost', SERVER_PORT))


# def send_file(file_name, addr):
#   """sends file content for file with specified file_name to client"""
#   msg = open(file_name).read()
#   split_msg = [msg[i:i+PACKET_LEN] for i in range(0, len(msg), PACKET_LEN)]
#   # Sending Packets
#   for i, msg in enumerate(split_msg):
#     packet = Packet(check_sum=1, seq_num=i, data=msg)
#     S_SERVER.sendto(packet.bytes(), addr)
#     print("Replied with packet #%i:" % i, packet.bytes(), "To client: ", addr)

if __name__ == '__main__':
  server_protocol = sys.argv[1] if sys.argv[1] else 'gbn'
  probability = 0.3
  seed_num = 1000

  demux_handler = DemuxHandler(server_protocol, probability, seed_num)
  while True:
    PACKET, ADDR = S_SERVER.recvfrom(512) #Buffer_size = 512
    demux_handler.demux_or_create(packet=PACKET, address=ADDR)
