from threading import Thread, Timer
import queue
import logging
import sys

from .GoBackNSender import GoBackNSender
from Packet import Packet

WINDOW_SIZE = 10
TIMEOUT_TIME = 1
PACKET_LENGTH = 80*8

# Logger configs
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)



class GoBackNServer:
    """
    Main entry point for GoBackN Server
    """
    def __init__(self, client_entry, probabilty, seed_num):
        # self.sender = GoBackNSender(packets, WINDOW_SIZE, client_entry.address)
        self.client_entry = client_entry
        self.probabilty = probabilty
        self.seed_num = seed_num
    
    def start(self):
        """
        Starts the send/recieve loop of the GoBackN server
        """
        # get first packet that has the file name
        request_pkt = Packet(packet_bytes=self.client_entry.queue.get())
        file_name = request_pkt.data
        LOGGER.info('Recieved Request for file: {}'.format(file_name))
        packets = Packet.get_file_packets(file_name, PACKET_LENGTH, WINDOW_SIZE)

        sender = GoBackNSender(packets, WINDOW_SIZE, self.client_entry.client_address, self.probabilty, self.seed_num)

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
                LOGGER.info('{} recieved {}'.format('Ack' if ack_packet.is_ack else 'Data', ack_packet))
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
                LOGGER.info('Timeout')
                pass
