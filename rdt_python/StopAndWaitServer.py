from Packet import Packet
import socket
from collections import deque

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
        print("STOP AND WAIT SERVER HANDLER RUNNING..")
        # TODO handle inactive client
        while True:
            # TODO handle timeout here
            self.client_entry.e.wait()
            print("RECEIVED PACKET: ", self.client_entry.pkt)
            parsed_pkt = Packet(packet_bytes=self.client_entry.pkt)
            # first check if seq number is correct else drop
            if parsed_pkt.seq_num is not self.seq:
                self.client_entry.e.clear()
                continue
            # else check the packet type if data or acknowledgement
            if parsed_pkt.is_ack:
                self.seq = (self.seq + 1) % 2
                if self.file_packets_queue:
                    S_SERVER.sendto(
                        self.file_packets_queue.popleft().bytes(),
                        self.client_entry.client_address
                    )
                else:
                    print("FILE PACKETS ARE ALL SENT SUCCESSFULLY..")
                    break
            else:
                file_name = parsed_pkt.data
                self.file_packets_queue = deque(
                    Packet.get_file_packets(file_name, Packet.PACKET_LENGTH, 2)
                )
                S_SERVER.sendto(
                    self.file_packets_queue.popleft().bytes(),
                    self.client_entry.client_address
                )
            self.client_entry.e.clear()


def run_handler(entry):
    """ runs handler """
    # TODO: refactor that the threads runs on __init__ if this function
    # proves not to be needed
    server = StopAndWaitServer(entry)
    server.start()
