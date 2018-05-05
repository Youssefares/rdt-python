import socket
import time
from queue import Queue
from threading import Thread, Event
import logging
from Packet import Packet

WINDOW_SIZE = 5
# Logger configs
LOGGER = logging.getLogger(__name__)
TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)


class SelectiveRepeatClient:
    def __init__(self, client_address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(client_address)
        #self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rcv_base = 0
        self.pre_buffer = [None]*(2*WINDOW_SIZE)
        self.buffer = []

    def request_file(self, server_address, file_name, dst_file_name):
        """
        Request file from server using GoBackN protocol
        """

        # send request
        self.socket.sendto(Packet(seq_num=0, data=file_name).bytes(), server_address)
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
            # TODO: Add timeouts
            pkt = Packet(packet_bytes=recieved_queue.get())
            LOGGER.info('Recieved Packet {}'.format(pkt))

            self.process_received_packet(pkt, server_address)

            # check if last packet join the thread and exit
            if pkt.is_last_pkt:
                LOGGER.info('Last Packet recieved, creating file.')
                end_event.set()
                with open('recieved/'+dst_file_name, 'w') as f:
                    f.write(''.join(self.buffer))
                    break
                
    def recieve_packets(self, queue, end_event):
        LOGGER.info('Reciever Starting...')
        while not end_event.is_set():
            packet, _ = self.socket.recvfrom(512)
            LOGGER.info('Packet Recieved {}'.format(packet))
            queue.put(packet)

    def process_received_packet(self, pkt, server_address):
        if pkt.seq_num in range(self.rcv_base, self.rcv_base+WINDOW_SIZE):
            if pkt.is_last_pkt:
                self.pre_buffer[pkt.seq_num] = pkt.data[:-1]
            else:
                self.pre_buffer[pkt.seq_num] = pkt.data
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=pkt.seq_num, data='').bytes(), server_address)
        if pkt.seq_num in range(self.rcv_base-WINDOW_SIZE, self.rcv_base):
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=pkt.seq_num, data='').bytes(), server_address)

        if pkt.seq_num == self.rcv_base:
            self.slide_buffer()

    def slide_buffer(self):
        new_base = self.rcv_base
        for i in range(self.rcv_base, 2*WINDOW_SIZE):
            if self.pre_buffer[i] is None:
                break
            self.buffer.append(self.pre_buffer[i])
            self.pre_buffer[i] = None
            new_base = (new_base + 1) % (2*WINDOW_SIZE)
        self.rcv_base = new_base


if __name__ == '__main__':
    client = SelectiveRepeatClient(('localhost', '5757'))
    client.request_file()