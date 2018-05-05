"""
This module implements a simple demultiplexer to handle multiple client
connections on top of a single UDP Connection
"""

from threading import Thread, Event, active_count
import socket
from queue import Queue
import logging

import StopAndWaitServer
from GoBackN.GoBackNServer import GoBackNServer
from SelectiveRepeat.SelectiveRepeatServer import SelectiveRepeatServer

# Logger configs
LOGGER = logging.getLogger(__name__)
TERIMAL_HANDLER = logging.StreamHandler()
TERIMAL_HANDLER.setFormatter(logging.Formatter(">> %(asctime)s:%(threadName)s:%(levelname)s:%(module)s:%(message)s"))
TERIMAL_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(TERIMAL_HANDLER)

class SWEntry:
    __slots__ = ['e', 'pkt', 'client_address']

    def __init__(self, e, pkt, client_address):
        self.e = e
        self.pkt = pkt
        self.client_address = client_address

    def get_tuple(self):
        return self.e, self.pkt, self.client_address


class GBNEntry:
    __slots__ = ['queue', 'client_address']

    def __init__(self, queue, client_address):
        self.queue = queue
        self.client_address = client_address
    
    def get_tuple(self):
        return self.queue, self.client_address

class SREntry:
    __slots__ = ['queue', 'client_address']

    def __init__(self, queue, client_address):
        self.queue = queue
        self.client_address = client_address
    
    def get_tuple(self):
        return self.queue, self.client_address

class DemuxHandler:
    """
    This class is responsible for demultiplexing requests from clients
    to the proper thread or creating a thread if non exists for this client

    Attributes:
        server_type: one of values ('sw', 'gbn', 'sr')
        threads_table: threads table structure depends on the type of server
            if 'sw'
                threads_table element : SWEntry(
                    e: EventObject
                    pkt: newest packet received
                )

    """
    def __init__(self, server_type='sw'):
        self.server_type = server_type
        self.threads_table = dict()

    def demux_or_create(self, packet, address):
        """
        Demultiplex the client request to the proper thread or create one
        if new connection
        :param packet: packet received from client
        :param address: client address (host, port) tuple
        :return: None
        """
        LOGGER.info("Packet Received from {}".format(address))
        if address in self.threads_table:
            LOGGER.debug("Passing {}'s request to existing Handler".format(address))
            # thread exists pass the new packet to the thread
            self._pass_packet(packet, address)
        else:
            # create new thread for this client
            if self.server_type == 'sw':
                LOGGER.debug("Creating a new SW Handler for {}".format(address))
                th_entry = self._get_new_SW_thread_table_entry(address)
                self.threads_table[address] = th_entry
                th = Thread(target=StopAndWaitServer.run_handler, args=[th_entry], daemon=True)
                th.setName('SW Thread # {}'.format(active_count()))
            
            elif self.server_type == 'gbn':
                LOGGER.debug("Creating a new GBN Handler for {}".format(address))
                th_entry = self._get_new_GBN_thread_table_entry(address)
                self.threads_table[address] = th_entry
                th = Thread(target=lambda client_entry: GoBackNServer(client_entry).start(), args=[th_entry], daemon=True)
            elif self.server_type == 'sr':
                LOGGER.debug("Creating a new SR Handler for {}".format(address))
                th_entry = self._get_new_SR_thread_table_entry(address)
                self.threads_table[address] = th_entry
                th = Thread(target=lambda client_entry: SelectiveRepeatServer(client_entry).start(), args=[th_entry], daemon=True)
            th.start()
            self._pass_packet(packet, address)

    def _pass_packet(self, packet, address):
        """
        Passes Packet to existing thread depending to the server type
        if server type is StopAndWait then pass it as an event else pass
        it in the shared queue
        :param packet: packet received from client
        :param address: thread/client address
        """
        shared_res = self.threads_table[address]
        if self.server_type == 'sw':
            # Wait until the last event was handled
            shared_res.e.set()
            shared_res.pkt = packet
        elif self.server_type == 'gbn':
            shared_res.queue.put(packet)
        elif self.server_type == 'sr':
            shared_res.queue.put(packet)

    def _get_new_SW_thread_table_entry(self, address):
        """
        setup thread table entry for new SW server thread
        :return: NamedTuple()
        """
        return SWEntry(e=Event(), pkt=None, client_address=address)

    def _get_new_GBN_thread_table_entry(self, address):
        return GBNEntry(queue=Queue(), client_address=address)

    def _get_new_SR_thread_table_entry(self, address):
        return SREntry(queue=Queue(), client_address=address)


    @staticmethod
    def _debug_dummy_server(entry):
        pkt_count = 0
        print("Server Thread running...")
        S_SERVER = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # S_SERVER.bind(('localhost', 6222))
        while True:
            e, pkt, client_address = entry.get_tuple()
            e.wait()
            print("PACKET #{}, {}".format(pkt_count, pkt))
            # S_SERVER.sendto(bytearray('Ack', encoding='utf-8'), client_address)
            pkt_count += 1
            e.clear()
