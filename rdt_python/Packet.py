"""This module provides packet class"""

from hashlib import md5
from math import floor
import os

EOT_CHR = chr(23)

class Packet:
    """
    data packet class
    """
    PACKET_LENGTH = 80
    def __init__(self, seq_num=None, data=None, packet_bytes=None):
        if packet_bytes:
            # Assumes 16 byte (32 hex digits) checksum as calculated by md5
            print("BYTES: ")
            print(packet_bytes)
            check_sum = packet_bytes[:32].decode('utf-8')
            self.seq_num = packet_bytes[32]
            self.len = packet_bytes[33]
            self.data = packet_bytes[34:].decode('utf-8')
            print("DATA: ")
            print(len(self.data))
            if check_sum != self.check_sum():
                raise ValueError("Packet corrupt: Checksum values don't match")
        else:
            if len(data) > 500:
                raise ValueError("Data should be less than 500 bytes")
            self.len = len(data)
            self.seq_num = seq_num
            self.data = data

        self.is_ack = len(self.data) == 0
        self.is_last_pkt = self.data[-1] == EOT_CHR if not self.is_ack else None

    def __str__(self):
        return str({self.seq_num: self.data})

    def __repr__(self):
        return str(self)

    def bytes(self):
        """ return packet in form of bytes"""
        return self.check_sum().encode('utf-8') + bytes([self.seq_num, self.len])\
        + self.data.encode('utf-8')

    def check_sum(self):
        """
        calculate check_sum
        >>> p1 = Packet(0, 'dsfdsfdsfdsfsdfsdf')
        >>> p2 = Packet(1, 'dsfdsfdsfsdfsdfsdf')
        >>> p1_again = Packet(0, 'dsfdsfdsfdsfsdfsdf')
        >>> p1.check_sum() != p2.check_sum()
        True
        >>> p1.check_sum() == p1_again.check_sum()
        True
        """
        return md5(bytes([self.seq_num, self.len])+ self.data.encode('utf-8')).hexdigest()


    @staticmethod
    def get_file_packets(file, packet_len, window_size):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        print(file)
        print(root_dir)
        packet_chars = floor(packet_len / 8)
        packets = []
        with open('{}/{}'.format(root_dir, file), 'r') as f:
            # TODO: Memory will be violated if file is large enough
            file = f.read()
            i = 0
            file_length = len(file)
            seq_num = 0
            while i < len(file):
                remaining_length = file_length - i
                packets.append(Packet(seq_num=seq_num, data=file[i:i+min(packet_chars, remaining_length)]))
                i += min(packet_chars, remaining_length)
                seq_num = (seq_num + 1) % window_size

            if len(packets[-1].data) < packet_chars:
                print(packets[-1].data)
                packets[-1].data += EOT_CHR
            else:
                packets.append(Packet(seq_num=seq_num, data=EOT_CHR))
        return packets



if __name__ == "__main__":
    import doctest
    doctest.testmod()
