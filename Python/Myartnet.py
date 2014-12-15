#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Name: luminosus ArtNet library
# Python ArtNet library to send and receive ArtNet data
# Author: Tim Henning

# Copyright 2013 Tim Henning
# Luminosus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Luminosus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import struct
import threading
import random
import time

version = 2.99

class Test():
    def run_test(self):
        artnet = ArtNet()
        artnet.daemon = True
        artnet.start()
        time.sleep(5)
        print artnet.own_ip
        print artnet.get_nodes()
        # artnet.join()

class ArtNet(threading.Thread):
    
    # default values
    hibernate = False
    socket_open = False
    address = (0, 0) # subnet, net
    use_unicast = False
    ignore_local_data = True
    data_length = 512
    universe_count = 1
    universes = [bytearray([0] * 513),]
    # own_ip = "192.168.178.20"
    # own_ip = "192.168.5.124"
    own_ip = "0.0.0.0"
    nodes = []
    
    def __init__(self, address=(0, 0), hibernate=False, use_unicast=False, ignore_local_data=True, data_length=512):
        threading.Thread.__init__(self)
        
        # set method parameter values
        subnet, net = address
        if 0 <= subnet <= 15 and 0 <= net <= 127:
            self.address = (subnet, net)
        self.hibernate = hibernate
        self.use_unicast = use_unicast
        self.set_output_mode()
        self.ignore_local_data = ignore_local_data
        self.data_length = data_length
        
        # for simplicity and speed this ArtNet implementation only works with multiplies of 512 channels
        if data_length % 512:
            print "Data length must be a multiple of 512."
            return False
        # prepare data buffer
        self.universe_count = data_length / 512
        self.universes = []
        for i in xrange(16):
            self.universes.append(bytearray([0] * 513))
        
        # set random ip if ip_check failures
        # self.own_ip = "192.168.178.20"
        # random value to identify ip_checK_packet
        self.ip_check_id = random.randint(1, 1024)
        
        # nodes list
        self.nodes = []
        
        # prebuild packages and headers for faster access
        self.build_packages()
    
                                                    ############ Flow Control ###############
    
    def run(self):
        sleep = time.sleep
        while True:
            # check for network connection
            if not self.hibernate:
                if not self.socket_open:
                    self.open_socket()
                if self.socket_open:
                    # self.set_own_ip()
                    self.ArtPoll()
                    self.server()
            # wait to check again for hibernate and possibility to open socket
            sleep(1)
    
    def open_socket(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(("", 6454))
            # self.s.bind((self.own_ip, 6454))
            self.s.sendto("ping", ("<broadcast>", 60000))
            self.socket_open = True
            return True
        except:
            try:
                self.s.close()
            except:
                pass
            self.socket_open = False
            print "Missing network connection."
            return False
    
    def start_hibernate(self):
        self.hibernate = True
        self.kill_server()
        self.set_output_mode()
    
    def stop_hibernate(self):
        self.hibernate = False
        self.set_output_mode()
    
    def close(self):
        self.kill_server()
        print "ArtNet node stopped."
    
                                                    ############ Server ###############
    
    def server(self):
        # prepare
        opcode_ArtDMX = 0x5000
        opcode_ArtPoll = 0x2000
        opcode_ArtPollReply = 0x2100
        opcode_ip_check = 0x6464
        opcode_kill = 0x9999
        recvfrom = self.s.recvfrom
        # start
        print "ArtNet node started."
        while True:
            data, addr = recvfrom(4096)
            # print ".... Data in ...."
            if data[:8] != 'Art-Net\x00':
                continue
            opcode = struct.unpack('<H', data[8:10])[0]
            print "Received OpCode: %#x" % opcode
            if opcode == opcode_ArtDMX:
                self.handle_ArtDMX(data, addr)
            elif opcode == opcode_ArtPoll:
                self.handle_ArtPoll(data, addr)
            elif opcode == opcode_ArtPollReply:
                self.handle_ArtPollReply(data, addr)
            elif opcode == opcode_ip_check:
                self.handle_ip_check(data, addr)
            elif opcode == opcode_kill:
                if data[12:] == str("luminosus_kill_signal_%s" % self.ip_check_id):
                    print "stop server"
                    break
            else:
                print "Received unknown package. OpCode: %s" % opcode
        # clean up
        self.s.close()
        self.socket_open = False
        print "ArtNet node stopped."

    def handle_ArtDMX(self, data, addr):
        if self.ignore_local_data and addr[0] == self.own_ip:
            return False
        p_subnet = ord(data[14]) >> 4
        p_universe = ord(data[14]) - (p_subnet << 4)
        p_net = ord(data[15])
        if p_net != self.address[1] or p_subnet != self.address[0]:
            return False
        data_length = struct.unpack('>H', data[16:18])[0]
        self.universes[p_universe][1:data_length +1] = [ord(i) for i in data[18:]]

    def handle_ArtPoll(self, data, addr):
        if addr[0] != self.own_ip and addr not in self.nodes:
            self.nodes.append(addr)
        self.ArtPollReply()
    
    def handle_ArtPollReply(self, data, addr):
        if addr[0] != self.own_ip and addr not in self.nodes:
            self.nodes.append(addr)
    
    def handle_ip_check(self, data, addr):
        if data[12:] == str("luminosus_ip_check_%s" % self.ip_check_id):
            self.own_ip = addr[0]
            print "IP of this ArtNet Node: %s" % self.own_ip
            for addr in self.nodes[:]:
                if addr[0] == self.own_ip:
                    self.nodes.remove(addr)
            self.build_ArtPollReply()
    
    def set_own_ip(self):
        self.s.sendto(self.ip_check_content, ('<broadcast>', 6454))
    
    def ArtPoll(self):
        self.s.sendto(self.ArtPoll_content, ("<broadcast>", 6454))
        
    def ArtPollReply(self):
        self.s.sendto(self.ArtPollReply_content, ("<broadcast>", 6454))
    
    def add_artnet_node(self, node_ip):
        if node_ip not in self.nodes:
            self.nodes.append((node_ip, 6454))
            return True
        else:
            return False

    def refresh_nodes(self):
        self.ArtPoll()
        return True

    def kill_server(self):
        content = []
        # id8, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtDMX -> 0x5000, Low Byte first
        content.append(struct.pack('<H', 0x9999))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # luminosus ip check
        content.append("luminosus_kill_signal_%s" % self.ip_check_id)
        content = ''.join(content)
        self.s.sendto(content, ('<broadcast>', 6454))

                                                    ############ Getter / Setter ###############

    def set_address(self, address):
        subnet, net = address
        if 0 <= subnet <= 15 and 0 <= net <= 127:
            self.address = address
            self.build_packages()
            return True
    
    def get_nodes(self):
        return self.nodes
    
    def get_subnet_data(self):
        return self.universes
        
                                                    ############ Send Data ###############
    
    def set_unicast(self, unicast=True):
        self.use_unicast = unicast
        self.set_output_mode()
    
    def set_output_mode(self):
        if not self.hibernate:
            if  self.use_unicast:
                self.send_dmx_data = self.ArtDMX_unicast
            else:
                self.send_dmx_data = self.ArtDMX_broadcast
        else:
            self.send_dmx_data = self.ArtDMX_dummy
        return True

    def ArtDMX_dummy(self, dmxdata, universe=0):
        pass
    
    def ArtDMX_unicast(self, dmxdata, universe=0):
        """ Data must be 1 * 512 0-255 int values. """
        content = bytearray(self.header_list[universe])
        # DMX Data
        content.extend(dmxdata)
        # send
        for addr in self.nodes:
            self.s.sendto(content, addr)
        
    
    def ArtDMX_broadcast(self, dmxdata, universe=0):
        """ Data must be 1 * 512 0-255 int values. """
        content = bytearray(self.header_list[universe])
        # DMX Data
        content.extend(dmxdata)
        # send
        self.s.sendto(content, ('<broadcast>', 6454))
    
    def send_data(self, data):
        """ Data must be data_length 0-1 float values. """
        if len(data) != self.data_length:
            return False
        

        d = 255
        data = [int(v * d) for v in data]
        

        for i in xrange(self.universe_count):
            self.send_dmx_data(data[i*512 : (i+1)*512], i)
        
        
                                                    ############ Header / Packet Contents ############
        
    def build_packages(self):
        self.build_ArtPoll()
        self.build_ArtPollReply()
        self.build_ip_check()
        
        self.header_list = []
        for u in xrange(16):
            self.header_list.append(self.get_ArtDMX_header(u))
    
    def get_ArtDMX_header(self, universe=0, eternity_port=1):
        header = []
        # Name, 7byte + 0x00
        header.append("Art-Net\x00") #8
        # OpCode ArtDMX -> 0x5000, Low Byte first
        header.append(struct.pack('<H', 0x5000)) #2
        # Protocol Version 14, High Byte first
        header.append(struct.pack('>H', 14)) #2
        # Order -> nope -> 0x00
        header.append("\x00") #1
        # Eternity Port
        header.append(chr(eternity_port)) #1
        # Address
        #universe, subnet, net = self.address
        subnet, net = self.address
        header.append(struct.pack('<H', net << 8 | subnet << 4 | universe)) #2
        # Length of DMX Data per packet, High Byte First
        header.append(struct.pack('>H', 512))
        header = "".join(header)
        header = bytearray(header)
        return header
        
    def build_ArtPoll(self):
        content = []
        # Name, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtPoll -> 0x2000, Low Byte first
        content.append(struct.pack('<H', 0x2000))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # TalkToMe
        # bit oriented data
        #   7   not used
        #   6   " transmit as Zero
        #   5   "
        #   4   "
        #   3   1 if Diagnostics messages are unicast / 0 for broadcast
        #   2   1 send me diagnostics messages / 0 Do not send me diag mess
        #   1   0   Only send ArtPollReply in response to an ArtPoll or ArtAddress.
        #       1   Send ArtPollReply whenever Node conditions change.
        #           This selection allows the Controller to be informed of
        #           changes without the need to continuously poll
        #   0   0
        #
        content.append(struct.pack('>H', 0b00000010))
        # Priority 
        content.append(chr(0xe0))           # DpCritical 
        self.ArtPoll_content = "".join(content)
    
    def build_ip_check(self):
        content = []
        # id8, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtDMX -> 0x5000, Low Byte first
        content.append(struct.pack('<H', 0x6464))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # luminosus ip check
        content.append("luminosus_ip_check_%s" % self.ip_check_id)
        self.ip_check_content = ''.join(content)
    
    def build_ArtPollReply(self):
        content = []
        # Name, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtPollReply -> 0x2100, Low Byte first
        content.append(struct.pack('<H', 0x2100))
        # Protocol Version 14, High Byte first
        # content.append(struct.pack('>H', 14))  # <- not in ArtPollReply
        # IP
        ip = [int(i) for i in self.own_ip.split('.')]
        content += [chr(i) for i in ip]
        # Port
        content.append(struct.pack('<H', 0x1936))
        # Firmware Version
        content.append(struct.pack('>H', 200))
        # Net and subnet of this node
        content.append(chr(self.address[1]))
        content.append(chr(self.address[0]))
        # OEM Code (E:Cue 1x DMX Out)
        content.append(struct.pack('>H', 0x0360))
        # UBEA Version -> Nope -> 0
        content.append(chr(0))
        # Status1
        content.append(struct.pack('>B', 0b11010000))
        # Manufacture ESTA Code
        content.append('LL')
        # Short Name
        content.append('luminosus-server2\x00')
        # Long Name
        content.append('luminosus-server2_ArtNet_Node' + '_' * 34 + '\x00')
        # Node Report
        # NumPortHi
        # NumPortLow
        # PortType[4]
        # Good Input[4]
        # Good Output[4]
        # Swin[4]
        # SwOut[4]
        # SwVideo
        # SwMacro
        # SwRemote
        # Spare
        # Spare
        # Spare
        # Style
        # MAC Hi
        # MAC
        # MAC
        # MAC
        # MAC
        # MAC Low
        # BindIp[4]
        # BindIndex
        # Status2
        # Filler
        
        # stitch together
        self.ArtPollReply_content = ''.join(content)
        #print self.lang['send_ArtPollReply']

if __name__ == "__main__":
    Test().run_test()
