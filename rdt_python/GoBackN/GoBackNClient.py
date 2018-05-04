import socket
import time
from queue import Queue
from threading import Thread
from Packet import Packet

WINDOW_SIZE = 5

class GoBackNClient:
    def __init__(self, client_address):
        self.recieve_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recieve_socket.bind(client_address)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def request_file(self, server_address, file_name):
        """
        Request file from server using GoBackN protocol
        """
        buffer = []
        last_recieved = -1
        to_be_recieved = 0

        # start queue reciving thread
        recieved_queue = Queue()
        recieve_thread = Thread(target=self.recieve_packets, args=[recieved_queue])

        # keep recieving packets and break if the last packet had a EOT
        while True:
            # TODO: Add timeouts
            pkt = Packet(packet_bytes=self.recieve_packets.get())
            if pkt.seq_num == to_be_recieved:
                # Add the packet data to the buffer
                buffer.append(pkt.data)
                last_recieved = to_be_recieved
                to_be_recieved = (to_be_recieved + 1) % (2 * WINDOW_SIZE)
                # check if last packet join the thread and exit
            else:
                # send ack for last recieved packet
                self.send_socket.sendto(Packet(seq_num=last_recieved, data=''))
                
    def recieve_packets(self, queue):
        while True:
            packet, _ = self.recieve_socket.recvfrom(512)
            queue.put(Packet(packet_bytes=packet))

if __name__ == '__main__':
    client = GoBackNClient(('localhost', '5757'))