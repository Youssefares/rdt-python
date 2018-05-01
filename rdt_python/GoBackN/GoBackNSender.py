"""Module containing Sender for GoBackNserver"""
import socket

class GoBackNSender:
    """Sender for GoBackNserver"""
    def __init__(self, packets, window_size, client_address):
        self.window_size = window_size
        self.packets = packets
        self.send_base = 0
        self.next_seq_num = 1
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_address = client_address

    def window(self):
        """
        return list of packets within window
        """
        return self.packets[self.send_base: self.send_base + self.window_size]

    # Debug functions
    def sent_acked(self):
        """
        returns list of packets that were sent and acked
        """
        return self.packets[:self.send_base]

    def sent_not_acked(self):
        """
        returns list of packets that were sent and not acked
        """
        return self.packets[self.next_seq_num:self.next_seq_num]

    def not_sent_not_acked(self):
        """
        returns list of packets that weren't sent or acked
        """
        return self.packets[self.next_seq_num:]

    def send_packets_in_window(self):
        """
        sends packets in the window one by one to the client
        """
        for pkt in self.window():
            self.socket.sendto(pkt.bytes(), self.client_address)
        self.next_seq_num += self.window_size

    def slide(self, last_acked_seq_num):
        """
        Updates class pointers and window according to last acked_seq_num
        """
        for i, pkt in enumerate(self.packets[self.send_base:]):
            if last_acked_seq_num == pkt.seq_num:
                self.send_base = self.send_base + i + 1
