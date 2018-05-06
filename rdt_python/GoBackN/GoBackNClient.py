import socket
import time
from queue import Queue
from threading import Thread, Event
import logging

from Packet import Packet
from helpers.Simulators import get_corrupt_simulator
from config import client_config

CONFIG_FILE = "inputs/client.in"
_, _, _, _, WINDOW_SIZE = client_config(CONFIG_FILE)

# Logger configs
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)


class GoBackNClient:
    def __init__(self, client_address, probability, seed_num):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(client_address)
        self.corrupt_or_not = get_corrupt_simulator(probability, seed_num)

    def request_file(self, server_address, file_name, save_file_name):
        """
        Request file from server using GoBackN protocol
        """
        buffer = []
        last_recieved = -1
        to_be_recieved = 0

        # send request
        self.socket.sendto(Packet(seq_num=0, data=file_name).bytes(), server_address)
        LOGGER.info('File request sent, File name: {}'.format(file_name))
        self.start_time = time.time()
        
        # start queue reciving thread
        recieved_queue = Queue()
        end_event = Event()
        recieve_thread = Thread(target=self.recieve_packets, args=[recieved_queue, end_event])
        recieve_thread.start()


        # keep recieving packets and break if the last packet had a EOT
        LOGGER.info('Starting Recieve Loop.')

        pkt = None
        while True:
            try:
                pkt = Packet(packet_bytes=self.corrupt_or_not(recieved_queue.get()))
                LOGGER.info('Recieved Packet {}'.format(pkt))
            except ValueError:
                LOGGER.info("Packet {} is corrupted".format(pkt))
                self.socket.sendto(Packet(seq_num=last_recieved, data='').bytes(), server_address)

            if pkt.seq_num == to_be_recieved:
                LOGGER.info('Packet is in sequence, adding it to buffer.')
                # Add the packet data to the buffer
                buffer.append(pkt.data)
                # send ack for this packet
                self.socket.sendto(Packet(seq_num=to_be_recieved, data='').bytes(), server_address)

                last_recieved = to_be_recieved
                to_be_recieved = (to_be_recieved + 1) % (2 * WINDOW_SIZE)

                # check if last packet join the thread and exit
                if pkt.is_last_pkt:
                    self.end_time = time.time()
                    LOGGER.info('Last Packet recieved, creating file.')
                    end_event.set()
                    with open('recieved/'+save_file_name, 'w') as f:
                        f.write(''.join(buffer))
                    LOGGER.info('File Recieved Successfully.. Exiting')
                    LOGGER.info("Time elapsed: {}".format(self.end_time-self.start_time))
                    break

            else:
                LOGGER.warning('An out-of-sequence packet recieved. ', pkt)
                # send ack for last recieved packet
                self.socket.sendto(Packet(seq_num=last_recieved, data='').bytes(), server_address)
                
    def recieve_packets(self, queue, end_event):
        LOGGER.info('Reciever Starting...')
        while not end_event.is_set():
            packet, _ = self.socket.recvfrom(512)
            LOGGER.info('Packet Recieved {}'.format(packet))
            queue.put(packet)

if __name__ == '__main__':
    client = GoBackNClient(('localhost', '5757'))
    client.request_file()
