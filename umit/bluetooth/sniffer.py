from basesniff import *

def parse_macs(mac_add):
    """
        Returns a list of integers representing that MAC address (len = 6)
        Parameters:
        
        - `mac_add`: string representation of a Bluetooth MAC address
    """
    import re
    p = re.compile(r'([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2})')
    m = p.match(mac_add)
    maclist = []
    if(m and len(m.groups()) == 6):
        for i in range(1, 6 + 1):
            maclist.append(int(m.group(i), 16)) #base 16 representation
    else:
        raise UmitBTError("Invalid mac address: " + mac_add) #raise an error here. invalid mac address
    return maclist

def main():

    # Process command line arguments.
    from optparse import OptionParser
    parser = OptionParser() 
        
    parser.add_option("-z", action="store_true", dest="ignore_zero", default=False,
                          help='Ignore zero length packets')
    parser.add_option('-d', action='store', type='string', dest='device',
                          help='<dev> e.g. hci0')
    parser.add_option('-t', action='store_true', dest='timer', default=False,
                          help ='timer')
    parser.add_option('-f', action='store', dest='filter', type='int', 
                          help='<filter>')
    parser.add_option('-s', action='store_true', dest='stop', default=False,
                          help='stop')
    parser.add_option('-S', action='store', dest='start', default=False,
                          help='<master@slave>')
    parser.add_option('-i', action='store', dest='ignore_type',
                          help='<ignore type>')
    parser.add_option('-e', action='store_true', dest='snif', default=False,
                          help='sniff')
    parser.add_option('-w', action='store', dest='dump', type='string',
                          help='<dump_to_file>')
    parser.add_option('-p', action='store', dest='pin', 
                          help='own pin')
    (options, args) = parser.parse_args()
    
    state = State()
    
    if not options.device:
        exit("Did not specify device")
    
    if options.timer:
        print "Timer: %x" % get_timer(state, options.device)
    
    if options.filter and options.filter >  -1:
        set_filter(state, options.device, options.filter)
    
    if options.stop:
        stop_sniff(state, options.device)
    
    if options.start:
        at_ind = options.start.find('@')
        if(not at_ind == -1):
            master_add = parse_macs(options.start[0:at_ind])
            slave_add = parse_macs(options.start[at_ind + 1:])
            print 'master = ', master_add, " slave = ", slave_add
            start_sniff(state, options.device, master_add, slave_add)
    
    if options.snif:
        sniff(state, options.device)
  
  
if __name__=='__main__':
    main()
   
