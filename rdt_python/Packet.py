"""This module provides packet class"""

from hashlib import md5

class Packet:
    """
    data packet class
    """
    def __init__(self, seq_num=None, data=None):
        if len(data) > 500:
            raise Exception("Data should be less than 500 bytes")
        self.len = len(data)
        self.seq_num = seq_num
        self.data = data


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
