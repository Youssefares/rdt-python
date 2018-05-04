import socket
import time
from queue import Queue
from threading import Thread, Event
import logging

from Packet import Packet

WINDOW_SIZE = 5

class GoBackNClient:
    def __init__(self, client_address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(client_address)
        #self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logging.getLogger('gbn_client')
        # TODO: this should be in the main client
        self.logger.addHandler(logging.StreamHandler())

    def request_file(self, server_address, file_name):
        """
        Request file from server using GoBackN protocol
        """
        buffer = []
        last_recieved = -1
        to_be_recieved = 0

        # send request
        self.socket.sendto(Packet(seq_num=0, data=file_name).bytes(), server_address)
        print('File Request sent')
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('File request sent, File name: {}'.format(file_name))

        # start queue reciving thread
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

            if pkt.seq_num == to_be_recieved:
                self.logger.info('Packet is to be recieved.')
                # Add the packet data to the buffer
                buffer.append(pkt.data)
                # send ack for this packet
                self.socket.sendto(Packet(seq_num=to_be_recieved, data='').bytes(), server_address)

                last_recieved = to_be_recieved
                to_be_recieved = (to_be_recieved + 1) % (2 * WINDOW_SIZE)

                # check if last packet join the thread and exit
                if pkt.last_pkt:
                    self.logger.info('Last Packet recieved, creating file.')
                    end_event.set()
                    with open(''+file_name.split('/')[-1], 'w') as f:
                        f.write(''.join(buffer))

            else:
                self.logger.info('An out-of-sequence packet recieved.')
                # send ack for last recieved packet
                self.socket.sendto(Packet(seq_num=last_recieved, data='').bytes(), server_address)
                
    def recieve_packets(self, queue, end_event):
        self.logger.info('Reciever Starting...')
        while not end_event.is_set():
            packet, _ = self.socket.recvfrom(512)
            self.logger.info('Packet Recieved {}'.format(packet))
            queue.put(packet)

if __name__ == '__main__':
    client = GoBackNClient(('localhost', '5757'))
    client.request_file()