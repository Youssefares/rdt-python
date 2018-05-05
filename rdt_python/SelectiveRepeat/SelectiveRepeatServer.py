from threading import Thread, Timer
import queue
import logging

from Packet import Packet

WINDOW_SIZE = 5
TIMEOUT_TIME = 10
PACKET_LENGTH = 80

class SelectiveRepeatServer:
    """
    Main entry point for SelectiveRepeat Server
    """
    def __init__(self, client_entry):
        self.client_entry = client_entry
        self.send_base = 0
        self.next_seq_num = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_address = self.client_entry.client_address
        self.timers_lock = threading.Lock() 

    def send_packet(self, i, pkt):
        """
        Sends packet in selective repeat window with timeout
        """
        self.sendto(pkt.bytes(), self.client_address)
        with self.timers_lock:
            timer = Timer(TIMEOUT_TIME, self.send_packet, args=[i])
            self.threads_and_timers[i][1] = timer
            timer.start()

    
    def start(self):
        """
        Starts the send/receive loop of the Selective Repeat server
        """
        # get first packet that has the file name
        request_pkt = Packet(packet_bytes=self.client_entry.queue.get())
        file_name = request_pkt.data
        self.logger.info('Recieved Request for file: {}'.format(file_name))
        
        # List of packets
        packets = Packet.get_file_packets(file_name, PACKET_LENGTH, WINDOW_SIZE)
        # List of packet sequence numbers
        packets_sequences = [pkt.seq_num for pkt in packets]
        # List of threads and timers for every packet in window
        # FIXME: Too much memory
        self.threads_and_timers = [
          Thread(target=self.send_packet,args=[i, packets[i]]),
          Timer(TIMEOUT_TIME, self.send_packet, args=[i, packets[i]]) 
          for pkt in packets
        ]

        # While there are things to send
        while self.send_base < len(packets):
            sent = 0
            for thread, _ in self.threads_and_timers[self.next_seq_num: min(self.send_base+WINDOW_SIZE, len(packets))]:
                thread.start()
                sent += 1
            self.next_seq_num += sent
            try:
                # stop sending ack'ed packets in the window
                ack_packet = Packet(packet_bytes=self.client_entry.queue.get())
                
                # look for seq_num in window (packets starting at send_base)
                # .. raises ValueError if find doesn't find seq_num
                index = packets_sequences.find(ack_packet.seq_num, self.send_base, min(self.send_base+WINDOW_SIZE, len(packets)))
                with self.timers_lock:
                    _, timer = self.threads_and_timers[index]
                    timer.stop()
                    self.threads_and_timers[index] = None

                # sliding
                if ack_packet.seq_num == self.send_base:
                    for i in range(self.send_base, min(self.send_base+WINDOW_SIZE, len(packets))):
                        with self.timers_lock:
                            if self.threads_and_timers[i] is None:
                                self.send_base += 1
                                

            # No acks maybe in yet
            except queue.Empty:
                pass

            # Acked sequence number may not be in range
            except ValueError:
                pass