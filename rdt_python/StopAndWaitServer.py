from Packet import Packet
import socket
import logging
from collections import deque

# Logger configs
LOGGER = logging.getLogger(__name__)
TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

class StopAndWaitServer:
    """
    Implementation of the StopAndWait protocol for handling
    client request
    """
    def __init__(self, client_entry):
        """
        :param client_entry: SWEntry
        """
        self.client_entry = client_entry
        self.seq = 0
        self.file_packets_queue = None

    def start(self):
        """
        Transfer the requested file to the client
        """
        S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        LOGGER.info("STOP AND WAIT SERVER HANDLER RUNNING..")
        # TODO handle inactive client
        while True:
            # TODO handle timeout here
            self.client_entry.e.wait()
            LOGGER.info("RECEIVED PACKET: {}".format(self.client_entry.pkt))
            parsed_pkt = Packet(packet_bytes=self.client_entry.pkt)
            # first check if seq number is correct else drop
            if parsed_pkt.seq_num is not self.seq:
                LOGGER.warning("Recieved packet out of sequence {}".format(Packet))
                self.client_entry.e.clear()
                continue
            # else check the packet type if data or acknowledgement
            if parsed_pkt.is_ack:
                LOGGER.info("Recieved Ack for packet seq {}".format(parsed_pkt.seq_num))
                self.seq = (self.seq + 1) % 2
                if self.file_packets_queue:
                    S_SERVER.sendto(
                        self.file_packets_queue.popleft().bytes(),
                        self.client_entry.client_address
                    )
                else:
                    LOGGER.info("FILE PACKETS ARE ALL SENT SUCCESSFULLY..")
                    break
            else:
                LOGGER.info("Recieved File Request for file {}".format(parsed_pkt.data))
                file_name = parsed_pkt.data
                self.file_packets_queue = deque(
                    Packet.get_file_packets(file_name, Packet.PACKET_LENGTH, 1)
                )
                S_SERVER.sendto(
                    self.file_packets_queue.popleft().bytes(),
                    self.client_entry.client_address
                )
                self.seq = 1
                
            self.client_entry.e.clear()


def run_handler(entry):
    """ runs handler """
    # TODO: refactor that the threads runs on __init__ if this function
    # proves not to be needed
    server = StopAndWaitServer(entry)
    server.start()
