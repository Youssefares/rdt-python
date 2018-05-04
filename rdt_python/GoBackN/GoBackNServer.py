from threading import Thread
import queue

from .GoBackNSender import GoBackNSender
from Packet import Packet

WINDOW_SIZE = 5
TIMEOUT_TIME = 2
PACKET_LENGTH = 80


class GoBackNServer:
    """
    Main entry point for GoBackN Server
    """
    def __init__(self, client_entry):
        # self.sender = GoBackNSender(packets, WINDOW_SIZE, client_entry.address)
        self.client_entry = client_entry
    
    def start(self):
        """
        Starts the send/recieve loop of the GoBackN server
        """
        # get first packet that has the file name
        request_pkt = Packet(packet_bytes=self.client_entry.queue.get())
        file_name = request_pkt.data
        packets = Packet.get_file_packets(file_name, PACKET_LENGTH, WINDOW_SIZE)

        sender = GoBackNSender(packets, WINDOW_SIZE, self.client_entry.client_address)

        oldest_unacked = 0
        while True:
            # request sender to send window to client
            Thread(target=sender.send_packets_in_window, daemon=True).start()

            try:
                # while there's no acks in the queue or timeout for oldest unacked packet
                ack_packet = Packet(packet_bytes=self.client_entry.queue.get(timeout=TIMEOUT_TIME))
                # TODO: Handle the fact that this seq number may not be in the window
                oldest_unacked = (ack_packet.seq_number + 1) % (2 * WINDOW_SIZE)
                sender.slide(ack_packet.seq_number)
            except ValueError:
                # this means that the ack is not valid so we ignore it
                # TODO: change time out to handle this case
                pass
            except queue.Empty:
                Thread(target=sender.send_packets_in_window, daemon=True).start()
