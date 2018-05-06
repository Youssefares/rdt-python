from Packet import Packet
import socket
import logging
from collections import deque
from helpers.Simulators import get_loss_simulator
from threading import Timer

# Logger configs
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

# Configs
TIMEOUT = 1

class StopAndWaitServer:
    """
    Implementation of the StopAndWait protocol for handling
    client request
    """
    def __init__(self, client_entry, probability, seed_num, close_connection_callback):
        """
        :param client_entry: SWEntry
        """
        self.client_entry = client_entry
        self.seq = 0
        self.file_packets_queue = None
        self.drop_current = get_loss_simulator(probability, seed_num)
        self.timer = None
        self.close_connection_callback = close_connection_callback

    def start(self):
        """
        Transfer the requested file to the client
        """
        S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        LOGGER.info("STOP AND WAIT SERVER HANDLER RUNNING..")
        # TODO handle inactive client
        while True:
            self.client_entry.e.wait()
            LOGGER.info("RECEIVED PACKET: {}".format(self.client_entry.pkt))
            parsed_pkt = Packet(packet_bytes=self.client_entry.pkt)

            # check the packet type if data or acknowledgement
            if parsed_pkt.is_ack:
                # first check if seq number is correct else drop
                if parsed_pkt.seq_num is not self.seq:
                    LOGGER.warning("Recieved packet out of sequence {}".format(Packet))
                    self.client_entry.e.clear()
                    continue

                LOGGER.info("Recieved Ack for packet seq {}".format(parsed_pkt.seq_num))
                self.timer.cancel()
                self.seq = (self.seq + 1) % 2
                if len(self.file_packets_queue):
                    self.send_packet_and_set_timer(self.file_packets_queue.popleft(), S_SERVER)
                else:
                    LOGGER.info("FILE PACKETS ARE ALL SENT SUCCESSFULLY..")
                    self.timer.cancel()
                    # close connection in Demux
                    self.close_connection_callback()
                    break
            else:
                LOGGER.info("Recieved File Request for file {}".format(parsed_pkt.data))
                file_name = parsed_pkt.data
                self.file_packets_queue = deque(
                    Packet.get_file_packets(file_name, Packet.PACKET_LENGTH, 1)
                )
                # S_SERVER.sendto(
                #     self.file_packets_queue.popleft().bytes(),
                #     self.client_entry.client_address
                # )
                self.send_packet_and_set_timer(self.file_packets_queue.popleft(), S_SERVER)
                self.seq = 1

            self.client_entry.e.clear()

    def send_packet_and_set_timer(self, pkt, server_socket):
        drop = self.drop_current()
        if drop:
            LOGGER.warning("Packet seq {} is lost".format(pkt.seq_num))
        else:
            LOGGER.info("Packet {} is sent".format(pkt))
            server_socket.sendto(pkt.bytes(), self.client_entry.client_address)
        
        self.timer = Timer(TIMEOUT, self.send_packet_and_set_timer, args=[pkt, server_socket])
        self.timer.start()
        
        return not drop

def run_handler(entry, probability, seed_num, close_connection_callback):
    """ runs handler """
    server = StopAndWaitServer(entry, probability, seed_num, close_connection_callback)
    server.start()
