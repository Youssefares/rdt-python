import socket
import time
from queue import Queue
from threading import Thread, Event
import logging
from Packet import Packet

WINDOW_SIZE = 5

class SelectiveRepeatClient:
    def __init__(self, client_address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(client_address)
        #self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logging.getLogger('gbn_client')
        # TODO: this should be in the main client
        self.logger.addHandler(logging.StreamHandler())

        self.rcv_base = 0
        self.pre_buffer = [None]*(2*WINDOW_SIZE)
        self.buffer = []

    def request_file(self, server_address, file_name):
        """
        Request file from server using GoBackN protocol
        """

        # send request
        self.socket.sendto(Packet(seq_num=0, data=file_name).bytes(), server_address)
        print('File Request sent')
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('File request sent, File name: {}'.format(file_name))

        # start queue receiving thread
        recieved_queue = Queue()
        end_event = Event()
        recieve_thread = Thread(target=self.recieve_packets, args=[recieved_queue, end_event])
        recieve_thread.start()


        # keep recieving packets and break if the last packet had a EOT
        self.logger.info('Starting Recieve Loop.')
        while True:
            # TODO: Add timeouts
            pkt = Packet(packet_bytes=recieved_queue.get())
            self.logger.info('Recieved Packet {}'.format(pkt))

            self.process_received_packet(pkt, server_address)

            # check if last packet join the thread and exit
            if pkt.last_pkt:
                self.logger.info('Last Packet recieved, creating file.')
                end_event.set()
                with open(''+file_name.split('/')[-1], 'w') as f:
                    f.write(''.join(buffer))
                
    def recieve_packets(self, queue, end_event):
        self.logger.info('Reciever Starting...')
        while not end_event.is_set():
            packet, _ = self.socket.recvfrom(512)
            self.logger.info('Packet Recieved {}'.format(packet))
            queue.put(packet)

    def process_received_packet(self, pkt, server_address):
        if pkt.seq_num in range(self.rcv_base, self.rcv_base+WINDOW_SIZE):
            self.pre_buffer[pkt.seq_num] = pkt.seq_num
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=to_be_recieved, data='').bytes(), server_address)
        if pkt.seq_num in range(self.rcv_base-N, self.rcv_base):
            # send ack for this packet
            self.socket.sendto(Packet(seq_num=to_be_recieved, data='').bytes(), server_address)

        if pkt.seq_num == self.rcv_base:
            self.slide_buffer(rcv_base)

    def slide_buffer(self):
        new_base = rcv_base
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