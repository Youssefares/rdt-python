from threading import Thread, Timer
import queue
import logging
import sys

from .GoBackNSender import GoBackNSender
from Packet import Packet

WINDOW_SIZE = 50
TIMEOUT_TIME = 1
PACKET_LENGTH = 80*8


class GoBackNServer:
    """
    Main entry point for GoBackN Server
    """
    def __init__(self, client_entry):
        # self.sender = GoBackNSender(packets, WINDOW_SIZE, client_entry.address)
        self.client_entry = client_entry
        self.logger = logging.getLogger('gbn_server')
        self.logger.addHandler(logging.StreamHandler())
    
    def start(self):
        """
        Starts the send/recieve loop of the GoBackN server
        """
        # get first packet that has the file name
        request_pkt = Packet(packet_bytes=self.client_entry.queue.get())
        file_name = request_pkt.data
        self.logger.info('Recieved Request for file: {}'.format(file_name))
        packets = Packet.get_file_packets(file_name, PACKET_LENGTH, WINDOW_SIZE)

        sender = GoBackNSender(packets, WINDOW_SIZE, self.client_entry.client_address)

        oldest_unacked = 0
        # request sender to send window to client
        Thread(target=sender.send_packets_in_window, daemon=True).start()
        
        # start timer for lastest unacked element
        t = Timer(TIMEOUT_TIME, sender.send_packets_in_window)
        t.start()

        while len(sender.window()):
            try:
                # while there's no acks in the queue or timeout for oldest unacked packet
                ack_packet = Packet(packet_bytes=self.client_entry.queue.get())
                self.logger.info('Ack recieved {}'.format(ack_packet))
                print('Ack recieved {}'.format(ack_packet))
                # TODO: When the seq number recieved is out of seq (one that was sent)
                # TODO: Handle the fact that this seq number may not be in the window
                oldest_unacked = (ack_packet.seq_num + 1) % (2 * WINDOW_SIZE)
                sender.slide(ack_packet.seq_num)
                
                # restart the time
                t.cancel()
                t = Timer(TIMEOUT_TIME, sender.send_packets_in_window)
                t.start()
            except ValueError:
                # this means that the ack is not valid so we ignore it
                # TODO: change time out to handle this case
                self.logger.info('Timeout')
                pass
