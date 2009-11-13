#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Abhiram Kasina <abhiram.casina@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import sys, os, os.path
import gtk, gobject
import re

from umit.pm.backend import MetaPacket
from umit.pm.backend.scapy import *

class Filter():
    
    def __init__(self, filter):
        self.filter_string = filter




    def evaluate(self, postfix): 
        stack = []
        postfix.reverse()
        for j in range(0, len(postfix)):
            i = len(postfix)-1-j
            if postfix[i] == True or postfix[i] == False:
                stack.append(postfix[i])
            elif postfix[i] == 'or':
                p1 = stack.pop() 
                p2 = stack.pop()
                stack.append(p1 or p2)
            elif postfix[i] == 'and':
                p1 = stack.pop() 
                p2 = stack.pop()
                stack.append(p1 and p2)
                
        return stack[0]

    def is_packet_valid(self, packet):
        stack = []
        postfix = []
        g = Tokenizer(self.filter_string )
        while True :
            tok = g.next()
            if tok == '':
                break
            elif tok == '(':
                stack.append(tok)
            elif tok == ')': 
                popped = stack.pop() 
                while not popped == '(':
                    postfix.append(popped)
                    popped = stack.pop() 
                    
            elif tok == 'and':
                stack.append(tok)
            elif tok == 'or':
                stack.append(tok)
            if tok == 'ip.src' or \
               tok == 'ip.dst' or \
               tok == 'ip.version'  or \
               tok == 'ip.ihl'  or \
               tok == 'ip.tos'  or \
               tok == 'ip.len'  or \
               tok == 'ip.flags'  or \
               tok == 'ip.frag'  or \
               tok == 'ip.ttl'  or \
               tok == 'ip.options'  or \
               tok == 'ip.checksum'  or \
               tok == 'ip.proto'  or \
               tok == 'tcp.sport'  or \
               tok == 'tcp.dport'  or \
               tok == 'tcp.seq'  or \
               tok == 'tcp.ack'  or \
               tok == 'tcp.window'  or \
               tok == 'tcp.chksum'  or \
               tok == 'tcp.urgptr'  or \
               tok == 'tcp.flags':
                token = g.next()
                if token == '':
                    break
                elif token == '==':
                    token = g.next()
                    if token == '':
                        break
                    if str(packet.get_field(tok)) != token:
                        postfix.append(False)
                    else:
                        postfix.append(True)
                elif token == '<=':
                    token = g.next()
                    if token == '':
                        break
                    if int(packet.get_field(tok)) > int(token):
                        postfix.append(False)
                    else:
                        postfix.append(True)
                elif token == '>=':
                    token = g.next()
                    if token == '':
                        break
                    if int(packet.get_field(tok)) < int(token):
                        postfix.append(False)
                    else:
                        postfix.append(True)
        while not len(stack) == 0:
            postfix.append(stack.pop())

        return self.evaluate(postfix)
                
    
                    
#TODO Need to ask nopper for IP flags thing
        

class Tokenizer():
    
    def __init__ (self, mstring):
        self.mstring = str(mstring)
        self.tokens = []
        regxs = ['(\()', '(\))',  #{,} \
             '(and)(\(|\s)', '(or)(\(|\s)',  # and, or \
             '([a-zA-Z]+\.[a-zA-Z]+)(\=\=|\<\=|\>\=|\!\=|\)|\s)',  # field name \
             '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',  # ip \
             '([a-zA-Z0-9]+)',  #alphanumeric \
             '(\=\=)', '(\>\=)', '(\<\=)', '(\!\=)'] # comparators
        while not mstring == '':
            for regx in regxs:
                m = re.split(regx, mstring, 1)
                if m[0] == '':
                    self.tokens.append(m[1])
                    mstring = m[2]
                    if len(m)>3:
                        mstring = mstring+m[3]
#                    #print regx
#                    #print m
                    break
            if not mstring == '':
                m = re.split('\s', mstring, 1) #skip whitespaces
                if m[0] == '':
                    mstring = m[1]
                
        # print self.tokens
        self.index = 0
    
    def next(self):
        if self.index < len(self.tokens):
            self.index = self.index+1
            return self.tokens[self.index-1]
        return ''
    
    
        
    
if __name__ == "__main__":
    f = Filter('((ip.dst==10.109.10.2)     and tcp.sport <= 9) or ip.src == 10.109.10.1')
    
   # f = Filter("ip.dst  ==")
    m = MetaPacket(Ether() / IP(src = '10.109.10.2' , dst = '10.109.10.2') /  TCP(sport = 10, flags = 'S'))
    print m.get_field('tcp.flags')
    m = MetaPacket(Ether() / IP(src = '10.109.10.2' , dst = '10.109.10.2') /
        TCP(sport = 10, flags = 'SA'))
    print m.get_field('tcp.flags')
    m = MetaPacket(Ether() / IP(src = '10.109.10.2' , dst = '10.109.10.2') /
        TCP(sport = 10, flags = 'A'))
    print m.get_field('tcp.flags')
   # print m.get_field('tcp.flags')
    print f.is_packet_valid(m)
    
