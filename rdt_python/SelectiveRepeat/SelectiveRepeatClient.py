import socket
import time
from queue import Queue
from threading import Thread, Event, Timer
import logging
from Packet import Packet
from helpers.window_range import window_range
from helpers.Simulators import get_corrupt_simulator
from config import client_config

CONFIG_FILE = "inputs/client.in"
_, _, _, _, WINDOW_SIZE = client_config(CONFIG_FILE)

TIMEOUT_TIME = 1
# Logger configs
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

class SelectiveRepeatClient:
    def __init__(self, client_address, probability, seed_num):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(client_address)
        #self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rcv_base = 0
        self.pre_buffer = [None]*(2*WINDOW_SIZE)
        self.buffer = []
        self.seq_nums = [i for i in range(WINDOW_SIZE*2)]
        self.corrupt_or_not = get_corrupt_simulator(probability, seed_num)
        LOGGER.info("WINDOW_SIZE: {}".format(WINDOW_SIZE))

    def send_file_name(self, server_address, file_name_packet):
      self.socket.sendto(file_name_packet.bytes(), server_address)
      self.timer = Timer(TIMEOUT_TIME, self.send_file_name, args=[server_address, file_name_packet])
      self.timer.start()
      
    def request_file(self, server_address, file_name, dst_file_name):
        """
        Request file from server using GoBackN protocol
        """

        # send request
        file_name_packet = Packet(seq_num=0, data=file_name)
        self.send_file_name(server_address, file_name_packet)
        self.start_time = time.time()
        print('File Request sent')
        LOGGER.info('File request sent, File name: {}'.format(file_name))

        # start queue receiving thread
        recieved_queue = Queue()
        end_event = Event()
        recieve_thread = Thread(target=self.recieve_packets, args=[recieved_queue, end_event])
        recieve_thread.start()


        # keep recieving packets and break if the last packet had a EOT
        LOGGER.info('Starting Recieve Loop.')
        while True:
            try:
                pkt = Packet(packet_bytes=self.corrupt_or_not(recieved_queue.get()))
                self.timer.cancel()
                LOGGER.info('Recieved Packet {}'.format(pkt))
                self.process_received_packet(pkt, server_address)

                # check if last packet join the thread and exit
                if pkt.is_last_pkt:
                    self.end_time = time.time()
                    LOGGER.info('Last Packet recieved, creating file.')
                    LOGGER.info("Time elapsed: {}".format(self.end_time-self.start_time))
                    end_event.set()
                    with open('recieved/'+dst_file_name, 'w') as f:
                        f.write(''.join(self.buffer))
                        break
            except ValueError:
                LOGGER.info("Packet {} is corrupted (ignored)".format(pkt))

                
    def recieve_packets(self, queue, end_event):
        LOGGER.info('Reciever Starting...')
        while not end_event.is_set():
            packet, _ = self.socket.recvfrom(512)
            # LOGGER.info('Packet Recieved {}'.format(packet))
            queue.put(packet)

    def process_received_packet(self, pkt, server_address):
        LOGGER.info("rcv_window is in: {} ".format(list(window_range(self.rcv_base, WINDOW_SIZE))))
        if pkt.seq_num in window_range(self.rcv_base, WINDOW_SIZE):
            self.pre_buffer[pkt.seq_num] = pkt.data
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=pkt.seq_num, data='').bytes(), server_address)
            LOGGER.info("Sent Ack for Packet {}".format(pkt))
        if pkt.seq_num in range(self.rcv_base-WINDOW_SIZE, self.rcv_base):
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=pkt.seq_num, data='').bytes(), server_address)

        if pkt.seq_num == self.rcv_base:
            self.slide_buffer()

    def slide_buffer(self):
        new_base = self.rcv_base
        LOGGER.info(self.pre_buffer)
        for i in window_range(self.rcv_base, WINDOW_SIZE):
            if self.pre_buffer[i] is None:
                break
            self.buffer.append(self.pre_buffer[i])
            self.pre_buffer[i] = None
            new_base = (new_base + 1) % (2*WINDOW_SIZE)
        LOGGER.info("Slid rcv_base from {} to {}".format(self.rcv_base, new_base))
        self.rcv_base = new_base


if __name__ == '__main__':
    client = SelectiveRepeatClient(('localhost', '5757'))
    client.request_file()