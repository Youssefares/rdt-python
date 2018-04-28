from collections import namedtuple
import re
from math import floor


PACKET_DATA = namedtuple("packet_data", ['data', 'seq_number', 'check_sum', 'length', 'type', 'last_pkt'])
ACK_RE = re.compile(".*Ack\d+.*")
DATA_RE = re.compile("b'(.*)'")
LAST_RE = re.compile(".*(\x17)")

PACKET_LENGTH = 80

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
    last_pkt = LAST_RE.match(data) is not None
    print(str(data[-4:]), last_pkt)
    return PACKET_DATA(data=data, seq_number=pkt[1], check_sum=pkt[0], length=pkt[2],
                       type='Ack' if ACK_RE.match(data) else 'Data', last_pkt=last_pkt)

def create_pkt_from_data(seq_number, data):
    return bytes([1, seq_number, len(data)]) + (data.encode('utf-8') if isinstance(data, str) else data)

def get_file_packets(file, packet_len):
    packet_chars = floor(packet_len / 8)
    packets = []
    with open(file, 'rb') as f:
        # TODO: Memory will be violated if file is large enough
        file = f.read()
        i = 0
        file_length = len(file)
        while i < len(file):
            remaining_length = file_length - i
            packets.append(file[i:i+min(packet_chars, remaining_length)])
            i += min(packet_chars, remaining_length)

        if len(packets[-1]) < packet_chars:
            packets[-1] += bytes(chr(23), encoding='utf-8')
        else:
            packets.append(bytes(chr(23), encoding='utf-8'))
    return packets
