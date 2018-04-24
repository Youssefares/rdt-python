from collections import namedtuple
import re

PACKET_DATA = namedtuple("packet_data", ['data', 'seq_number', 'check_sum', 'length', 'type'])
ACK_RE = re.compile(".*Ack\d+.*")
DATA_RE = re.compile("b'(.*)'")

def is_packet_valid(pkt):
    """
    TODO: Implement this method to check for checksum if valid
    :param pkt: packet to validate
    :return: Boolean
    """
    return True

def get_data(pkt):
    """
    Parse packet and return its information
    :return namedtuple
    """
    data = DATA_RE.match(str(pkt[3:])).group(1)
    return PACKET_DATA(data=data, seq_number=pkt[1], check_sum=pkt[0], length=pkt[2],
                       type='Ack' if ACK_RE.match(data) else 'Data')

def create_pkt_from_data(seq_number, data):
    return bytes([1, seq_number, len(data)]) + data.encode('utf-8')
