from umit.pm.core.logger import log    
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

def smtp_dissector():
    SMTP_NAME = 'dissector.smtp'
    SMTP_PORTS = (25, )

    manager = AuditManager()
    sessions = SessionManager()
    
    
    
    
    
    def smtp(mpkt):
        if sessions.create_session_on_sack(mpkt, SMTP_PORTS, SMTP_NAME):
            return

        sess = sessions.is_first_pkt_from_server(mpkt, SMTP_PORTS, SMTP_NAME)

        if sess and not sess.data:
            payload = mpkt.data

            # Ok we have an SMTP banner over here
            if payload and payload.startswith('220'):
                banner = payload[4:].strip()
                mpkt.set_cfield('banner', banner)

                manager.user_msg('SMTP : %s:%d banner: %s' % \
                                 (mpkt.l3_src, mpkt.l4_src, banner),
                                 6, SMTP_NAME)

            sessions.delete_session(sess)
            return

        # Skip empty and server packets
        if mpkt.l4_dst not in SMTP_PORTS or not mpkt.data:
            return

        payload = mpkt.data.strip()

        #auth Login
    return smtp


class SMTPDissector(Plugin, PassiveAudit):
    
    def start(self, reader):
        self.dissector =smtp_dissector()

    def register_decoders(self):
        AuditManager().add_dissector(APP_LAYER_TCP, 25, self.dissector)

    def stop(self):
        AuditManager().remove_dissector(APP_LAYER_TCP, 25, self.dissector)
        
        
__plugins__ = [SMTPDissector]
__plugins_deps__ = [('SMTPDissector', ['TCPDecoder'], ['SMTPDissector-1.0'], []),]

__audit_type__ = 0
__protocols__ = (('tcp', 25), ('smtp', None))
__vulnerabilities__ = (('FTP dissector', {
    'description' : 'File Transfer Protocol (FTP) is a standard network '
                    'protocol used to exchange and manipulate files over an '
                    'Internet Protocol computer network, such as the Internet. '
                    'FTP is built on a client-server architecture and utilizes '
                    'separate control and data connections between the client '
                    'and server applications. Client applications were '
                    'originally interactive command-line tools with a '
                    'standardized command syntax, but graphical user '
                    'interfaces have been developed for all desktop operating '
                    'systems in use today. FTP is also often used as an '
                    'application component to automatically transfer files for '
                    'program internal functions. FTP can be used with '
                    'user-based password a While data is being transferred via '
                    'the data stream, the control stream sits idle. This can '
                    'cause problems with large data transfers through '
                    'firewalls which time out sessions after lengthy periods '
                    'of idleness. While the file may well be successfully '
                    'transferred, the control session can be disconnected by '
                    'the firewall, causing an error to be generated.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'File_Transfer_Protocol'), )
    }),
)
