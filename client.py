"""client"""

# Imports
import socket
import sys
from threading import Thread, Event
import select

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


REPLY_EVENT = Event()

def send_file_name(s_client):
  """ sends filename to se"""
  msg = FILE
  # Sending file name packet
  packet = Packet(check_sum=1, seq_num=1, data=msg)
  s_client.sendto(packet.bytes(), (SERVER_IP, SERVER_PORT))
  print("Sent:", packet.bytes())

  # Receive with timeout 5 seconds
  ready = select.select([s_client], [], [], 5)
  if ready[0]:
    packet, addr = s_client.recvfrom(512) #Buffer_size = 512
    print(packet)
    if addr == (SERVER_IP, SERVER_PORT):
      print("Reply received from: ", addr)
      # Broadcast reply_event to stop sending requests
      REPLY_EVENT.set()
      #TODO: keep receiving and ack'ing according to packet length

# Creating client socket
S_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_CLIENT.bind(('localhost', CLIENT_PORT))

# Keep sending file name, if no reply from server within 5 secs
while not REPLY_EVENT.is_set():
  SEND_THREAD = Thread(target=send_file_name, args=[S_CLIENT])
  SEND_THREAD.start()
  SEND_THREAD.join(timeout=5)
