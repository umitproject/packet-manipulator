"""
    This module used in PacketManipulator. Used to provide descriptions for 
    sniffed packets.

"""


__LMP_OP_TAGS =  { 124: 'LMP Escape 1',
                   125: 'LMP Escape 2',
                   126: 'LMP Escape 3',
                   127: {    1: 'LMP Accepted Ext',
                            17: 'LMP Channel Classification',
                            12: 'LMP eSCO Link Req',
                             3: 'LMP Features Req Ext',
                             4: 'LMP Features Res Ext',
                            25: 'LMP IO Capability Req',
                            26: 'LMP IO Capability Res',
                            23: 'LMP Pause Encrypt Req',
                            24: 'LMP Resume Encrypt Req',
                            27: 'LMP Numberic Comparison failed',
                             2: 'LMP Not Accepted Ext',
                            11: 'LMP Packet Type Table Req',
                            28: 'LMP Passkey Failed',
                            29: 'LMP OOB Failed',
                            30: 'LMP Keypress Notification',
                            13: 'LMP Remove eSCO Link Req'
                         },
                    3 : 'LMP Accepted',
                    11: 'LMP AU_RAND',
                    35: 'LMP Auto Rate',
                    5 : 'LMP Clock Offset Req',
                    6 : 'LMP Clock Offset Res',
                    9 : 'LMP COMB_KEY',
                    32: 'LMP Decrease Power Req',
                     7: 'LMP Detach',
                    65: 'LMP DHKey_Check',
                    61: 'LMP Encapsulated Header',
                    62: 'LMP Encapsulated Payload',
                    58: 'LMP Encryp_key_size_mask Req',
                    59: 'LMP Encryp_key_size_mask Res',
                    16: 'LMP Encryp_key_size Req',
                    15: 'LMP Encryp_mode Req',
                    39: 'LMP Features Req',
                    40: 'LMP Features Res',
                    51: 'LMP Host Connection Req',
                    20: 'LMP Hold',
                    21: 'LMP Hold Req',
                    31: 'LMP Increase Power Req',
                     8: 'LMP IN_RAND',
                    33: 'LMP_MAX_POWER',
                    45: 'LMP_MAX_SLOT',
                    46: 'LMP MAX_SLOT Req',
                    34: 'LMP MIN_POWER',
                    28: 'LMP Modify Beacon',
                     1: 'LMP Name Req',
                     2: 'LMP Name Res',
                     4: 'LMP Not Accepted',
                    53: 'LMP Page Mode Req',
                    54: 'LMP Page Scan Mode Req',
                    25: 'LMP Park Req',
                    36: 'LMP Preferred Rate',
                    41: 'LMP Quality of Service',
                    42: 'LMP Quality of Service Req',
                    44: 'LMP Remove SCO Link Req',
                    43: 'LMP SCO Link Req',
                    60: 'LMP Set AFH',
                    27: 'LMP Set Broadcast Scan Window',
                    49: 'LMP Setup complete',
                    63: 'LMP Simple pairing confirm',
                    64: 'LMP Simple Pairing Number',
                    52: 'LMP Slot offset',
                    23: 'LMP Sniff Req',
                    12: 'LMP SRES',
                    17: 'LMP Start Encrypt Req',
                    18: 'LMP Stop Encrypt Req',
                    55: 'LMP Supervision Timeout',
                    19: 'LMP Switch Req',
                    13: 'LMP TEMP_RAND',
                    14: 'LMP TEMP_KEY',
                    56: 'LMP Test Activate',
                    57: 'LMP Test Control',
                    47: 'LMP Timing Accuracy Req',
                    48: 'LMP Timing Accuracy Res',
                    10: 'LMP Unit Key',
                    29: 'LMP Unpark_BD_ADDR Req'
                  }


def is_lmp(sniff_payload):
    header = sniff_payload.header if hasattr(sniff_payload, 'header') else None
    return header is not None and is_lmp_header(header)

def is_l2cap(sniff_payload):
    header = sniff_payload.header if hasattr(sniff_payload, 'header') else None
    return header is not None and is_l2cap_header(header)

def is_lmp_header(header):
    return hasattr(header, 'tid') and hasattr(header, 'op1')

def is_l2cap_header(header):
    return hasattr(header, 'length') and hasattr(header, 'chan_id')

def get_type_name(sniff_payload):
    if is_lmp(sniff_payload):
        return 'LMP'
    elif is_l2cap(sniff_payload):
        return 'L2CAP'
    else:
        return 'Unknown'

def get_summary(sniff_payload):
    if is_lmp(sniff_payload):
        header = sniff_payload.header
        op1, op2 = header.op1, header.op2
        
        if op1 == 127: 
            return __LMP_OP_TAGS[op1].get(op2, 'Escape 1')
        else:
            return __LMP_OP_TAGS.get(op1, '')
    else:
        return ''