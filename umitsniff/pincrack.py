'''
Created on 21-Jun-2009

@author: quekshuy
'''

import struct
from sniffcommon import *


PIN_DATA_LEN = 7
PIN_DATA_DEPTH = 16

GOT_IN_RAND = 1 << 1
GOT_COMB1 = 1 << 2
GOT_COMB2 = 1 << 3
GOT_AU_RAND1 = 1 << 4
GOT_SRES1 = 1 << 5
GOT_AU_RAND2 = 1 << 6
GOT_SRES2 = 1 << 7
#define GOT_IN_RAND    (1 << 1)
#define GOT_COMB1    (1 << 2)
#define GOT_COMB2    (1 << 3)
#define GOT_AU_RAND1    (1 << 4)
#define GOT_SRES1    (1 << 5)
#define GOT_AU_RAND2    (1 << 6)
#define GOT_SRES2    (1 << 7)


#uint8_t    s_pin; //whether protected by pin
#    uint8_t    s_pin_data[7][16];
#    int    s_pin_master;

def do_pin(state, op, data):
    
    #initialise state.pin_data
    state.pin_data = [0] * PIN_DATA_LEN
    for i in range(PIN_DATA_LEN):
        state.pin_data[i] = [0] * PIN_DATA_DEPTH
    unpack_data_for_pin = struct.unpack(`len(data)`+'B', data)
    
    try: 
        
        { # dispatch table
         LMP_IN_RAND: lmp_in_rand,
         LMP_COMB_KEY: lmp_com_key,
         LMP_AU_RAND: lmp_au_rand,
         LMP_SRES: lmp_sres \
         
         }[op](state, unpack_data_for_pin)
        
        if not state.pin == 0xFF:
            return
        print 'btpincrack Go ',
        if state.pin_master:
            print '<master> <slave> ',
        else:
            print '<slave> <master> ',
        
        for i in range(7):
            length = 4 if i >= 5 else 16
            for j in range(length):
                print "%.2X" % state.pin_data[i][j],
            print " ",
        print 
        state.pin = 1
             
    except UmitBTError:
        pass

def pindata_memcpy(state, lenindex, pin_data):
    state.pin_data[lenindex] = []
    map(lambda x: state.pin_data[lenindex].append(x), pin_data)

def lmp_in_rand(state, data):
    state.pin = 1 | GOT_IN_RAND
    state.pin_master = state.master
    state.pin_data[0] = []
    #map(lambda x: state.pin_data[0].append(x), pin_data)
    pindata_memcpy(state, 0, data)

def lmp_comb_key(state, data):
    
    if(not (state.pin & GOT_IN_RAND)):
        return
    
    if state.master == state.pin_master:
        state.pin_data[1] = []
#        map(lambda x: state.pin_data[1].append(x), 
#            struct.unpack(`len(data)` + 'B', data))
        pindata_memcpy(state, 1, data)
        state.pin |= GOT_COMB1
    else:
        state.pin_data[2] = []
        pindata_memcpy(state, 2, data)
        state.pin |= GOT_COMB2 

def lmp_au_rand(state, data):
    if ((not (state.pin & GOT_COMB1))
        or not(state.pin & GOT_COMB2)):
        return
    
    if state.master == state.pin_master:
        state.pin_data[3] = []
        pindata_memcpy(state, 3, data)
        state.pin |= GOT_AU_RAND1
    else:
        state.pin_data[4] = []
        pindata_memcpy(state, 4, data)
        state.pin |= GOT_AU_RAND2

def lmp_sres(state, data):
    if not state.master == state.pin_master:
        if not state.pin & GOT_AU_RAND1:
            return
        state.pin_data[6] = []
        pindata_memcpy(state, 6, data)
        state.pin |= GOT_SRES1
    else:
        if not state.pin & GOT_AU_RAND2:
            return
        state.pin_data[5] = []
        pindata_memcpy(state, 5, data)
        state.pin |= GOT_SRES2

    
    