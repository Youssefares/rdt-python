import socket
from config import client_config
from helpers import PacketHelper
import time

CONFIG_FILE = "../inputs/client.in"
PACKET_LEN = 50

SERVER_IP, SERVER_PORT, CLIENT_PORT, FILE, RCV_WINDOW_SIZE = client_config(
    CONFIG_FILE)

# TODO: Multiple clients on different ports
# Creating client socket
S_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_CLIENT.bind(('localhost', CLIENT_PORT))

def main_receive_loop(file_name):
    seq_number = 0
    pkt = PacketHelper.create_pkt_from_data(seq_number, file_name)
    while True:
        S_CLIENT.sendto(pkt, (SERVER_IP, SERVER_PORT))
        print("PACKET SEQ {} SENT...".format(seq_number))
        packet, address = S_CLIENT.recvfrom(512)
        time.sleep(0.5)
        print("RECEIVED PACKET: ", packet)
        pkt_data = PacketHelper.get_data(packet)
        if pkt_data.seq_number is not seq_number:
            # Last packet is not received
            continue
        # Acknowledge received packet
        pkt = PacketHelper.create_pkt_from_data(seq_number, 'Ack{}'.format(seq_number))
        seq_number = (seq_number + 1) % 2


if __name__ == '__main__':
    file_name = 'big_file.txt'
    main_receive_loop(file_name)