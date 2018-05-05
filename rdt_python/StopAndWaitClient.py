import socket
import time
import logging
from config import client_config
from Packet import Packet
from helpers.Simulators import get_loss_simulator

CONFIG_FILE = "inputs/client.in"
PACKET_LEN = 50

# Logger configs
logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

SERVER_IP, SERVER_PORT, CLIENT_PORT, FILE, RCV_WINDOW_SIZE = client_config(
    CONFIG_FILE)

# TODO: Multiple clients on different ports
# Creating client socket
S_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S_CLIENT.bind(('localhost', CLIENT_PORT))

def main_receive_loop(file_name, probability, seed_num):
    seq_number = 0
    buffer = []
    drop_current = get_loss_simulator(probability, seed_num)
    # FIXME: this becomes ack at times
    LOGGER.info("Starting Stop and Wait Client..")
    pkt = Packet(seq_num=seq_number, data=file_name)
    S_CLIENT.sendto(pkt.bytes(), (SERVER_IP, SERVER_PORT))
    LOGGER.info("File Request Sent.")

    while True:
        # FIXME: 512 should be el buffer size exactly
        packet, address = S_CLIENT.recvfrom(512)
        # Simulates network layer delay
        # time.sleep(0.5)
        LOGGER.info("RECEIVED PACKET: {}".format(packet))
        print("RECEIVED PACKET: {}".format(packet))
        recieved_pkt = Packet(packet_bytes=packet)

        if recieved_pkt.seq_num is not seq_number:
            # Last packet is not received
            print("OUT OF SEQ PACKET RECIEVED")
            S_CLIENT.sendto(pkt.bytes(), (SERVER_IP, SERVER_PORT))
            continue
        # Acknowledge received packet
        buffer.append(recieved_pkt.data)
        seq_number = (seq_number + 1) % 2
        ack_pkt = Packet(seq_num=seq_number, data='')
        if recieved_pkt.is_last_pkt:
            with open("recieved/{}".format(file_name.split('/')[-1]), 'w') as f:
                f.write(''.join(buffer))
            LOGGER.info("FILE RECEIVED AND SAVED...")
            print("FILE RECEIVED AND SAVED...")
            break

        S_CLIENT.sendto(ack_pkt.bytes(), (SERVER_IP, SERVER_PORT))
        LOGGER.info("PACKET SEQ {} SENT...".format(seq_number))

if __name__ == '__main__':
    file_name = 'public/small_file.txt'
    main_receive_loop(file_name, 0.3, 1000)