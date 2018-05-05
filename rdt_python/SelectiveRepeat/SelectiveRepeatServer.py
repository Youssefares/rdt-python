from threading import Thread, Timer, Lock
import queue
import logging
import socket

from Packet import Packet

WINDOW_SIZE = 5
TIMEOUT_TIME = 10
PACKET_LENGTH = 80

# Logger configs
LOGGER = logging.getLogger(__name__)
TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

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
        self.timers_lock = Lock() 

    def send_packet(self, i, pkt):
        """
        Sends packet in selective repeat window with timeout
        """
        self.socket.sendto(pkt.bytes(), self.client_address)
        LOGGER.info("Sent packet: {}".format(pkt))
        LOGGER.info("Waiting for lock to start timer again")
        with self.timers_lock:
            LOGGER.info("Acquired lock")
            timer = Timer(TIMEOUT_TIME, self.send_packet, args=[i, pkt])
            self.threads_and_timers[i][1] = timer
            timer.start()
        LOGGER.info("Released lock")


    
    def start(self):
        """
        Starts the send/receive loop of the Selective Repeat server
        """
        # get first packet that has the file name
        request_pkt = Packet(packet_bytes=self.client_entry.queue.get())
        file_name = request_pkt.data
        LOGGER.info('Recieved Request for file: {}'.format(file_name))
        
        # List of packets
        packets = Packet.get_file_packets(file_name, PACKET_LENGTH, WINDOW_SIZE)
        LOGGER.info("Sending file consisting of {} packets".format(len(packets)))
        # List of packet sequence numbers
        packets_sequences = [pkt.seq_num for pkt in packets]
        # List of threads and timers for every packet in window
        # FIXME: Too much memory
        self.threads_and_timers = [
          [Thread(target=self.send_packet,args=[i, pkt]),
          Timer(TIMEOUT_TIME, self.send_packet, args=[i, pkt])] 
          for i, pkt in enumerate(packets)
        ]

        # While there are things to send
        while self.send_base < len(packets):
            LOGGER.info("Entered sending loop with send_base: {}, next_seq_num: {}".format(self.send_base, self.next_seq_num))
            sent = 0
            for thread, _ in self.threads_and_timers[self.next_seq_num: min(self.send_base+WINDOW_SIZE, len(packets))]:
                thread.start()
                sent += 1
            self.next_seq_num += sent
            LOGGER.info("Sent {} packets".format(sent))
            try:
                # stop sending ack'ed packets in the window
                ack_packet = Packet(packet_bytes=self.client_entry.queue.get())
                LOGGER.info("Received ack_packet: ".format(ack_packet))
                # look for seq_num in window (packets starting at send_base)
                # .. raises ValueError if find doesn't find seq_num
                index = packets_sequences.index(ack_packet.seq_num, self.send_base, min(self.send_base+WINDOW_SIZE, len(packets)))
                
                LOGGER.info("Waiting for lock to stop timer")
                with self.timers_lock:
                    LOGGER.info("Acquired lock")
                    _, timer = self.threads_and_timers[index]
                    LOGGER.info("ack_packet in window, stopping timer")
                    timer.cancel()
                    self.threads_and_timers[index] = None
                LOGGER.info("Released lock")

                # sliding
                if ack_packet.seq_num == packets[self.send_base].seq_num:
                    old_send_base = self.send_base
                    for i in range(self.send_base, min(self.send_base+WINDOW_SIZE, len(packets))):
                        LOGGER.info("Waiting for lock to slide")
                        with self.timers_lock:
                            LOGGER.info("Acquired lock")
                            if self.threads_and_timers[i] is None:
                                self.send_base += 1
                        LOGGER.info("Released lock")
                    LOGGER.info("\n\n\nSlid send_base from {} to {}".format(old_send_base, self.send_base))
                                

            # No acks maybe in yet
            except queue.Empty:
                LOGGER.error("queue empty too many times")
                pass

            # Acked sequence number may not be in range
            except ValueError:
                LOGGER.error("ack_packet not in window, no effect")
                pass
        LOGGER.info("\n Done sending all {} packets".format(self.send_base))