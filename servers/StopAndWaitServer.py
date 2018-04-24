from helpers import PacketHelper
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
            parsed_pkt = PacketHelper.get_data(self.client_entry.pkt)
            # first check if seq number is correct else drop
            if parsed_pkt.seq_number is not self.seq:
                # send last ack
                S_SERVER.sendto(bytearray('Ack{}'.format((self.seq + 1) % 2),
                                          encoding='utf-8'), self.client_entry.client_address)
                self.client_entry.e.clear()
                continue
            # else check the packet type if data or acknowledgement
            if parsed_pkt.type == 'Ack':
                self.seq = (self.seq + 1) % 2
                if len(self.file_packets_queue):
                    S_SERVER.sendto(PacketHelper.create_pkt_from_data(self.seq, self.file_packets_queue.popleft()),
                                    self.client_entry.client_address)
                else:
                    print("FILE PACKETS ARE ALL SENT SUCCESSFULLY..")
                    break
            else:
                file_name = parsed_pkt.data
                self.file_packets_queue = deque(PacketHelper.get_file_packets(file_name, PacketHelper.PACKET_LENGTH))
                S_SERVER.sendto(PacketHelper.create_pkt_from_data(self.seq, self.file_packets_queue.popleft()),
                                self.client_entry.client_address)
            self.client_entry.e.clear()


def run_handler(entry):
    # TODO: refactor that the threads runs on __init__ if this function
    # proves not to be needed
    server = StopAndWaitServer(entry)
    server.start()
