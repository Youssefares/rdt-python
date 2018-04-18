"""This module provides packet class"""

class Packet:
  """
  data packet class
  """
  def __init__(self, check_sum, seq_num=None, data=None):
    if len(data) > 500:
      raise Exception("Data should be less than 500 bytes")
    self.check_sum = check_sum
    self.len = len(data)
    self.seq_num = seq_num
    self.data = data


  def bytes(self):
    """ return packet in form of bytes"""
    return bytes([self.check_sum, self.seq_num, self.len])\
      +self.data.encode('utf-8')
