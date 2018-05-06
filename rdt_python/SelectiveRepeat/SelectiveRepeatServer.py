from threading import Thread, Timer, Lock
import queue
import logging
import socket

from Packet import Packet
from helpers.Simulators import get_loss_simulator
from config import server_config

CONFIG_FILE = "inputs/server.in"
_, WINDOW_SIZE, _, _ = server_config(CONFIG_FILE)
TIMEOUT_TIME = 1
PACKET_LENGTH = 80*8

# Logger configs
LOGGER = logging.getLogger(__name__)

FILE_HANDLER = logging.FileHandler('logs/{}.txt'.format(__name__))
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)


class SelectiveRepeatServer:
    """
    Main entry point for SelectiveRepeat Server
    """
    def __init__(self, client_entry, probability, seed_num, close_connection_callback):
        self.client_entry = client_entry
        self.send_base = 0
        self.next_seq_num = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_address = self.client_entry.client_address
        self.timers_lock = Lock()
        self.drop_this_packet = get_loss_simulator(probability, seed_num)
        self.close_connection_callback = close_connection_callback
        LOGGER.info("WINDOW_SIZE: {}".format(WINDOW_SIZE))

    def send_packet(self, i, pkt):
        """
        Sends packet in selective repeat window with timeout
        """
        if self.drop_this_packet():
          LOGGER.info("Dropped packet: {}".format(pkt))
        else:
          self.socket.sendto(pkt.bytes(), self.client_address)
          LOGGER.info("Sent packet: {}".format(pkt))
        # LOGGER.info("Waiting for lock to start timer again")
        with self.timers_lock:
            # LOGGER.info("Acquired lock")
            timer = Timer(TIMEOUT_TIME, self.send_packet, args=[i, pkt])
            self.threads_and_timers[i][1] = timer
            timer.start()
        # LOGGER.info("Released lock")


    
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
                LOGGER.info("Received ack_packet: {}".format(ack_packet))
                # look for seq_num in window (packets starting at send_base)
                # .. raises ValueError if find doesn't find seq_num
                LOGGER.info("snd_window is in: {} ".format(packets_sequences[self.send_base: self.send_base+ WINDOW_SIZE]))
                index = packets_sequences.index(ack_packet.seq_num, self.send_base, min(self.send_base+WINDOW_SIZE, len(packets)))
                
                # LOGGER.info("Waiting for lock to stop timer")
                with self.timers_lock:
                    # LOGGER.info("Acquired lock")
                    _, timer = self.threads_and_timers[index]
                    LOGGER.info("ack_packet in window, stopping timer")
                    timer.cancel()
                    self.threads_and_timers[index] = None
                # LOGGER.info("Released lock")

                # sliding
                if ack_packet.seq_num == packets[self.send_base].seq_num:
                    old_send_base = self.send_base
                    d = {packets_sequences[self.send_base+i]: t_h for i, t_h in enumerate(self.threads_and_timers[self.send_base: min(self.send_base+WINDOW_SIZE, len(packets))])}
                    LOGGER.info("{}".format(d))
                    for i in range(self.send_base, min(self.send_base+WINDOW_SIZE, len(packets))):
                        # LOGGER.info("Waiting for lock to slide")
                        with self.timers_lock:
                            # LOGGER.info("Acquired lock")
                            if self.threads_and_timers[i] is None:
                                LOGGER.info("packet with seq_num #{} is None".format(packets_sequences[i]))
                                self.send_base += 1
                            else:
                              break
                        # LOGGER.info("Released lock")
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
        self.close_connection_callback()
