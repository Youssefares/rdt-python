"""Module containing Sender for GoBackNserver"""
import socket
import logging
import time

def log_when_called(mssg):
    def log_when_called_decorator(fn):
        def new_fn(*args, **kargs):
            print(mssg)
            fn(*args, **kargs)
        return new_fn
    return log_when_called_decorator


class GoBackNSender:
    """Sender for GoBackNserver"""
    def __init__(self, packets, window_size, client_address):
        self.window_size = window_size
        self.packets = packets
        self.send_base = 0
        self.next_seq_num = 1
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_address = client_address
        self.logger = logging.getLogger('gbn_sender')
        self.logger.addHandler(logging.StreamHandler())

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

    @log_when_called('Sending Packets in Window')
    def send_packets_in_window(self):
        """
        sends packets in the window one by one to the client
        """
        print("Window Length: ", len(self.window()))
        for pkt in self.window():
            # time.sleep(0.5)
            self.socket.sendto(pkt.bytes(), self.client_address)
            print("Packet {} sent".format(pkt))
        self.next_seq_num += self.window_size

    @log_when_called('Window Slide Called')
    def slide(self, last_acked_seq_num):
        """
        Updates class pointers and window according to last acked_seq_num
        """
        for i, pkt in enumerate(self.window()):
            if last_acked_seq_num == pkt.seq_num:
                self.send_base = self.send_base + i + 1
                print("HELODOSDOASODASDO >>>>> New Send Base: {} with seq {}".\
                    format(self.send_base, self.packets[self.send_base].seq_num))
                break

    def is_in_window(self, seq_num):
        """
        Checks if provided seq_num is in the window sent or not
        """
        for pkt in self.window():
            if seq_num == pkt.seq_num:
                return True
        return False
