import os, os.path

from umpa import protocols
from umpa.protocols.base import Protocol

# Globals UMPA protocols
gprotos = []

# Locals User defined protocols
lprotos = []

# We need to get all the protocols from the __path__
# of protocols and also import the protocols defined
# by the user from the .umit/umpa/ directory

def load_gprotocols():
    path = protocols.__path__[0]

    for fname in os.listdir(path):
        if not fname.lower().endswith(".py"):
            continue

        try:
            # We'll try to load this
            module = __import__("%s.%s" % (protocols.__name__,
                                fname.replace(".py", "")))
        except Exception, err:
            print "Ignoring exception", err

    # This is a dirty hack becouse we could have multiple
    # objects that derives protocols but aren't protocols
    # like private classes.
    return Protocol.__subclasses__()

def get_protocols():
    """
    @return a list of type [(Protocol, name)]
    """
    return gprotos

def get_proto(proto_name):
    for proto in gprotos:
        if proto.__name__ == proto_name:
            return proto

    for proto in lprotos:
        if proto.__name__ == proto_name:
            return proto

    print "Protocol named %s not found." % proto_name
    return None

def get_proto_name(proto_inst):
    return proto_inst.__class__.__name__

def get_field_name(proto_inst, field, trim_underscore=True):
    # TODO: we should ask for a name attribute in field object
    
    ret = None

    for f in proto_inst._ordered_fields:
        if proto_inst._fields[f] is field:
            ret = f
            break

    if ret and trim_underscore:
        return ret.replace("_", "")
    return ret

def get_field_desc(field):
    return field.__doc__

gprotos = load_gprotocols()
