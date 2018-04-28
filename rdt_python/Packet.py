"""This module provides packet class"""

from hashlib import md5

class Packet:
    """
    data packet class
    """
    def __init__(self, seq_num=None, data=None, packet_bytes=None):
        if packet_bytes:
            self.seq_num = packet_bytes[17]
            self.length = packet_bytes[18]
            self.data = packet_bytes[19:]

            check_sum = packet_bytes[:16].decode('utf-8')
            if check_sum != self.check_sum():
                raise Exception("Packet corrupt: Checksum values don't match")

        else:
            if len(data) > 500:
                raise Exception("Data should be less than 500 bytes")
            self.len = len(data)
            self.seq_num = seq_num
            self.data = data

    def __str__(self):
        return str({self.seq_num: self.data})

    def __repr__(self):
        return str(self)

    def bytes(self):
        """ return packet in form of bytes"""
        return bytes([self.check_sum(), self.seq_num, self.len])\
        +self.data.encode('utf-8')

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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
