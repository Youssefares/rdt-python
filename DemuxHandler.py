"""
This module implements a simple demultiplexer to handle multiple client
connections on top of a single UDP Connection
"""

from threading import Thread, Event, active_count
from collections import namedtuple


class SWEntry:
    __slots__ = ['e', 'pkt']

    def __init__(self, e, pkt):
        self.e = e
        self.pkt = pkt

    def get_tuple(self):
        return self.e, self.pkt


class DemuxHandler:
    """
    This class is responsible for demultiplexing requests from clients
    to the proper thread or creating a thread if non exists for this client

    Attributes:
        server_type: one of values ('sw', 'gbn', 'sr')
        threads_table: threads table structure depends on the type of server
            if 'sw'
                threads_table element : NamedTuple(
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
        print("PACKET RECEIVED FROM ", address)
        if address in self.threads_table:
            print("PASSING TO EXISTING HANDLER")
            # thread exists pass the new packet to the thread
            self._pass_packet(packet, address)
        else:
            # create new thread for this client
            if self.server_type == 'sw':
                print("CREATING NEW SERVER HANDLER")
                th_entry = self._get_new_SW_thread_table_entry()
                self.threads_table[address] = th_entry
                th = Thread(target=self._debug_dummy_server, args=[packet, th_entry], daemon=True)
                th.setName('SW Thread # {}'.format(active_count()))
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
            # while shared_res.e.is_set():
            #     pass
            print(shared_res.e)
            shared_res.e.set()
            shared_res.pkt = packet

    def _get_new_SW_thread_table_entry(self):
        """
        setup thread table entry for new SW server thread
        :return: NamedTuple()
        """
        return SWEntry(e=Event(), pkt=None)

    def _debug_dummy_server(self, packet, entry):
        pkt_count = 0
        print("Server Thread running...")
        while True:
            e, pkt = entry.get_tuple()
            e.wait()
            print("PACKET #{}, {}".format(pkt_count, packet))
            pkt_count += 1
            e.clear()
