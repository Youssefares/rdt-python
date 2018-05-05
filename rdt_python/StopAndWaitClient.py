import socket
import time

from config import client_config
from Packet import Packet

CONFIG_FILE = "inputs/client.in"
PACKET_LEN = 50

SERVER_IP, SERVER_PORT, CLIENT_PORT, FILE, RCV_WINDOW_SIZE = client_config(
    CONFIG_FILE)

# TODO: Multiple clients on different ports
# Creating client socket
S_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_CLIENT.bind(('localhost', CLIENT_PORT))

def main_receive_loop(file_name):
    seq_number = 0
    buffer = []
    # FIXME: this becomes ack at times
    pkt = Packet(seq_num=seq_number, data=file_name)
    while True:
        S_CLIENT.sendto(pkt.bytes(), (SERVER_IP, SERVER_PORT))
        print("PACKET SEQ {} SENT...".format(seq_number))
        # FIXME: 512 should be el buffer size exactly
        packet, address = S_CLIENT.recvfrom(512)
        # Simulates network layer delay
        # time.sleep(0.5)
        print("RECEIVED PACKET: ", packet)

        pkt_data = Packet(packet_bytes=packet)

        if pkt_data.seq_num is not seq_number:
            # Last packet is not received
            continue
        # Acknowledge received packet
        buffer.append(pkt_data.data)
        pkt = Packet(seq_num=seq_number, data='')
        seq_number = (seq_number + 1) % 2
        if pkt_data.is_last_pkt:
            with open("received/{}".format(file_name.split('/')[-1]), 'w+') as f:
                f.write(''.join(buffer))
            print("FILE RECEIVED AND SAVED...")
            break

if __name__ == '__main__':
    file_name = 'public/big_file.txt'
    main_receive_loop(file_name)