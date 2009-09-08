Audits framework
################

PM provides a complete framework to create in a simple way plugins to test
functionalities and vulnerabilities of your network. These plugins are called
**audits** and are organized in two categories:

* Passive audits
* Active audits

Passive audits are tests monitoring or listening in the activities of your
network segments. Typical examples of these audits are protocol decoders like
*Ethernet decoder*, *Wifi Decoder*, *TCP Decoder*, and protocol dissectors like 
*HTTP dissector*, *FTP dissector*, etc.

Active audits require, on the other hand, to write packets on the network
segment and furthermore the analysis of the possible replies. They are a
specialization of passive audits. Typical examples includes *ARP cache poison*,
*DNS spoof*, *Syn flooder*.

.. _activate-audits:

Activate audits
===============

Audits plugins could be enabled and configure by the Plugins windows accessible
by clicking **Options -> Plugins** menu and then **Audit page**.

The windows is organized in Passive and Active audits. You could enable one of 
that by clicking directly on the check next to the name of plugin.

The window offers four views to configure, find or consult the various audits
available:

* Show plugins view
* Information view
* Find plugins view
* Configure plugins view

Show plugins view
-----------------

This view shows the available plugins and let the user to enable an audit by
simple clicking on the check box.

    .. image:: static/half_Audits-show-view.png
       :align: center

Information view
----------------

This view shows informations related to protocols or vulnerabilities implemented
in the selected audit plugin.

    .. image:: static/half_Audits-info-view.png
       :align: center

Find plugins view
-----------------

This view let the user find a specified audit by searching for vulnerability
description, available references, class, protocol names, etc.

    .. image:: static/half_Audits-find-view.png
       :align: center

.. _configure-plugins-view:

Configure plugins view
----------------------

From this view the user could configure the behaviour of the selected audit. The
meaning of options are showed in a tooltip window on mouse hover.

    .. image:: static/half_Audits-configure-view.png
       :align: center

.. _passive-audits:

Passive Audits
==============

A common scope of passive audits is to analyze captured packets. To do so a
passive audit has to register a callback by using various methods provided by
:class:`AuditManager`, in order to obtain desired packets.

:class:`AuditManager` offers various methods to register different types of
callbacks. Essentially there are four categories of callbacks:

* :ref:`decoder-callback`
* :ref:`dissector-callback`
* :ref:`hook-callback`
* :ref:`injector-callback`

Passive audits could be runned within *Audit* or *Sniff* contexts and also on a
loaded file (PCAP). Make sure that two check boxes, respectively *Enable passive
audits on sniff* and *Enable passive audits on loaded files* are enabled in
*Preferences -> Backend -> Audits section* . Audits are enabled by default for 
*AuditContext* 's.

Passive audits uses *OutputTab* to show to the user useful informations. So be
sure to take a look at this window:

    .. image:: static/half_OutputTab.png
       :align: center

.. _decoder-callback:

Decoder callback
----------------

A decoder callback is used when the passive audit is going to provide decoding
functionalities for a certain protocol. *Ethernet decoder* or *UDP decoder*
are examples of these audits. They provide functions to decode protocols and
various controls like checksums comparing to provide extra information to the
chained decoders or dissectors.

.. _dissector-callback:

Dissector callback
------------------

A dissector callback is used to analyze the contents of packets captured. The
decode phase is already completed in the parent decoder. Examples of these
audits are *HTTP decoder* and *FTP decoder*. They provide functions to parse
payload of packets and to collect useful information, like passwords or service
banners.

.. _hook-callback:

Hook callback
-------------

Various audits may require to set a hook after or before the packet is decoded
or dissected for various reasons. These plugins could use a hook to have full
control over the decode or dissector phase. An example of plugin using hooks is
*OS Fingerprint* that places hooks to after TCP and IP decoding phase, in
order to provide remote os fingerprinting functionalities.

.. _injector-callback:

Injector callback
-----------------

Injector callback is used essentialy for hijacking and injection purposes in
active sessions. If you have implemented a decoder for a certain protocol, you
could provide an injector callback, that will be fired if the user would inject
data in an active session. Examples of plugins providing injection callbacks are
*TCP decoder* and *UDP decoder*.

Active Audits
=============

Active audits are a special case of :ref:`passive-audits` but also offers active
functionalities, like sending of crafted packets at Layer 2 or 3.

To do this they use various methods provided by :class:`AuditContext`. There are
various functions to get information about the current attack like IP of the
monitored interface, the netmask, the MAC, the MTU and functions to sent packets
in it like the *si_l\**, *sr_l\**, *s_l\** collections that permits to send, 
receive packets at various Layers (2, 3 or on the bridged inferface if
available).

Active audits could be loaded, like passive,from the Plugin Window (See also
:ref:`activate-audits`), but to be executed within an AuditSession they should
be triggered from *Audits* main menu entry, but be sure to have already open
an AuditSession and to be the selected tab, else the menu entry will be
disabled.

    .. image:: static/half_AuditSession.png
       :align: center

After having clicked on a menu entry an Input dialog could be showed to enter
parameters and configuration to run a particular audit on the opened
*AuditSession*. An example of this dialog is:

    .. image:: static/half_AuditInputs.png
       :align: center

Also check out the *Audit Output* perspective to check for messages
coming from online audits. All the messages, or selected ones could be saved
in a pratical log file (ASCII and XML output format available).

Configuration file
==================

Some audits require fine tuning of her configurations. You could do directly
from :ref:`configure-plugins-view`, or by editing ``audits-conf.xml`` XML file
in ``.PacketManipulator`` directory placed under your home folder.

For example *DNS spoof* may require a better configuration::

    <str id="records" description="UDP records">
        # Here you could insert DNS records
        # The syntax is:
        #  record type host
        # record: is a string like manipulator.umitproject.org or a wildcarded
        # string like *.umitproject.org.
        # type: could be A, MX, WINS, PTR (For PTR wildcarded record is not allowed)
        # host: is an IP address in dotted form or hostname
        *.microsoft.com A 66.66.66.66
    </str>


