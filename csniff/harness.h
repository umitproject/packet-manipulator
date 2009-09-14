
#ifndef HARNESS_H_
#define HARNESS_H_


#include <stdio.h>
#include <err.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>


#include "layers.h"
#include "btconstants.h"

void print_sniff_hdr(PySniffHdr *hdr, struct frontline_packet *fp) {

	if(hdr != NULL)  {
		printf("HEADER Hlen = %d, Clock = %d, Hdr0 = %d, DLen = %d, Timer = %d, Chan = %d, Seq = %d\n", hdr->hlen, hdr->clock,
				hdr->hdr0, hdr->dlen, hdr->timer,
				hdr->chan, hdr->seq);
	}

	if(fp != NULL)
	{
		printf("FP Hlen = %d, Clock = %d, Hdr0 = %d, DLen = %d, Timer = %d, Chan = %d, Seq = %d\n",
				fp->fp_hlen, fp->fp_clock, fp->fp_hdr0,
				fp->fp_len, fp->fp_timer, fp->fp_chan, fp->fp_seq);
	}

}


void hexdump(void *buf, int len)
{
	unsigned char *p = buf;

	while (len--)
		printf("%.2X ", *p++);
	printf("\n");
}


void dump_lmp(int state_s_dump, int state_s_master, void *buf, int len)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_EVENT_PKT;
	hci_event_hdr evt;
	unsigned char csr_lmp[1+1+17+1];
	int totlen = sizeof(type) + sizeof(evt) + sizeof(csr_lmp);
	unsigned char *p = csr_lmp;

	assert(len <= 17);
	if(state_s_dump == -1)
		return;
	/* hcidump header*/
	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	Py_BEGIN_ALLOW_THREADS
	if (write(state_s_dump, &dh, sizeof(dh)) != sizeof(dh))
		err(1, "write()");

	if (write(state_s_dump, &type, sizeof(type)) != sizeof(type))
		err(1, "write()");
	Py_END_ALLOW_THREADS

	/* event header */
	memset(&evt, 0, sizeof(evt));
	evt.evt		= EVT_VENDOR;
	evt.plen	= sizeof(csr_lmp);
	Py_BEGIN_ALLOW_THREADS
	if (write(state_s_dump, &evt, sizeof(evt)) != sizeof(evt))
		err(1, "write()");
	Py_END_ALLOW_THREADS
	/* CSRized LMP packet */
	memset(csr_lmp, 0, sizeof(csr_lmp));
	*p++ = 20; /* channel ID */
	*p++ = state_s_master ? 0x10 : 0x0f;
	memcpy(p, buf, len);
	p += 17;
	*p = 0; /* connection handle */
	assert(((unsigned long) p - (unsigned long) csr_lmp)< sizeof(csr_lmp));
	Py_BEGIN_ALLOW_THREADS
	if (write(state_s_dump, csr_lmp, sizeof(csr_lmp)) != sizeof(csr_lmp))
		err(1, "write()");
	Py_END_ALLOW_THREADS

}

void dump_l2cap(int state_s_dump, int state_s_llid, void *buf, int len)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_ACLDATA_PKT;
	hci_acl_hdr acl;
	int totlen = sizeof(type) + sizeof(acl) + len;

	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	if(state_s_dump == -1)
		return;

	Py_BEGIN_ALLOW_THREADS
	if (write(state_s_dump, &dh, sizeof(dh)) != sizeof(dh))
		err(1, "write()");
	if (write(state_s_dump, &type, sizeof(type)) != sizeof(type))
		err(1, "write()");
	memset(&acl, 0, sizeof(acl));
	acl.dlen	= len;
	acl.handle	= acl_handle_pack(0, state_s_llid);
	if (write(state_s_dump, &acl, sizeof(acl)) != sizeof(acl))
		err(1, "write()");

	if (write(state_s_dump, buf, len) != len)
		err(1, "write()");
	Py_END_ALLOW_THREADS
}


/*
 * Definiton for PySniffPacket. Garbage collection is important for this object,
 *
 */

/**
 *  Populate the SniffPacket fields
 */
//static void
//setup_PySniffPacket(PySniffPacket *self, struct frontline_packet *fp)
//{
//
//	self->llid  = (fp->fp_len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
//	self->bool_isFromMaster = PyBool_FromLong((long) !( fp->fp_clock & FP_SLAVE_MASK));
//	self->type = (fp->fp_hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK;
//	self->status = fp->fp_clock >> FP_STATUS_SHIFT;
//	self->chan = fp->fp_chan;
//	self->dlen = fp->fp_len >> FP_LEN_SHIFT;
//	self->seq = fp->fp_seq;
//	self->clock = fp->fp_clock & FP_CLOCK_MASK;
//}

//static int
//PySniffPacket_traverse(PySniffPacket *self, visitproc visit, void *arg)
//{
//	Py_VISIT(self->_payloadpkt);
//	return 0;
//}
//
//static int
//PySniffPacket_clear(PySniffPacket *self)
//{
//	PyObject *tmp;
//	tmp = self->_payloadpkt;
//	self->_payloadpkt = NULL;
//	Py_XDECREF(tmp);
//	return 0;
//}
//
//static PyObject *
//PySniffPacket_new(PyTypeObject *type, PyObject *args, PyObject *kwlist)
//{
//	PySniffPacket *self;
//	self = (PySniffPacket *) type->tp_alloc(type, 0);
//	if(self != NULL)
//	{
//		self->_csrpkt = NULL;
//		Py_INCREF(Py_None);
//		self->_payloadpkt = Py_None;
//	}
//	else
//		return NULL;
//
//	return (PyObject *)self;
//}
//
//static void
//PySniffPacket_dealloc(PySniffPacket *self)
//{
//
//	PySniffPacket_clear(self);
//	if(self->_csrpkt)
//		free(self->_csrpkt);
//
//	self->ob_type->tp_free((PyObject *) self);
//}
//
//
//static PyMemberDef PySniffPacket_members[] = {
//
//		{"llid", T_INT, offsetof(PySniffPacket, llid), 0, "LLID."},
//
//		{"fromMaster", T_OBJECT, offsetof(PySniffPacket, bool_isFromMaster),
//				0, "Indicates if packet is sent from master device."},
//
//		{"type", T_INT, offsetof(PySniffPacket, type), 0, "Type of packet."},
//
//		{"clock", T_UINT, offsetof(PySniffPacket, clock), 0, "Clock."},
//
//		// Status needs to be figured out first.
//		//{"status", T_INT, offsetof(PySniffPacket, status), 0, "Status. 0 is successful."},
//
//		{"plen", T_USHORT, offsetof(PySniffPacket, dlen), 0, "Payload length."},
//
//		//Not useful
//		//{"seq", T_UBYTE, offsetof(PySniffPacket, seq), 0, "Sequence number"},
//		{"channel", T_UBYTE, offsetof(PySniffPacket, chan), 0, "Channel number."},
//
//		{"payload", T_OBJECT, offsetof(PySniffPacket, _payloadpkt), 0, "Payload packet."},
//
//		{NULL}
//
//};
//
//
//static PyTypeObject PySniffPacketType =  {
//	   PyObject_HEAD_INIT(NULL)
//		0,                         /*ob_size*/
//		"sniff.SniffPacket",        /*tp_name*/
//		sizeof(PySniffPacket),      /*tp_basicsize*/
//		0,                         /*tp_itemsize*/
//		(destructor)PySniffPacket_dealloc, /*tp_dealloc*/
//		0,                         /*tp_print*/
//		0,                         /*tp_getattr*/
//		0,                         /*tp_setattr*/
//		0,                         /*tp_compare*/
//		0,                         /*tp_repr*/
//		0,                         /*tp_as_number*/
//		0,                         /*tp_as_sequence*/
//		0,                         /*tp_as_mapping*/
//		0,                         /*tp_hash */
//		0,                         /*tp_call*/
//		0,                         /*tp_str*/
//		0,                         /*tp_getattro*/
//		0,                         /*tp_setattro*/
//		0,                         /*tp_as_buffer*/
//		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
//		"PyState object will ultimately be converted into a SniffSession. This is struct state from the original code",           /* tp_doc */
//		(traverseproc) PySniffPacket_traverse,                          /* tp_traverse */
//		(inquiry) PySniffPacket_clear,                          /* tp_clear */
//		0,                          /* tp_richcompare */
//		0,                          /* tp_weaklistoffset */
//		0,                          /* tp_iter */
//		0,                          /* tp_iternext */
//		0,             				/* tp_methods */
//		PySniffPacket_members,      /* tp_members */
//		0 ,     					/* tp_getset */
//		0,                         /* tp_base */
//		0,                         /* tp_dict */
//		0,                         /* tp_descr_get */
//		0,                         /* tp_descr_set */
//		0,                         /* tp_dictoffset */
//	    0,				      		/* tp_init */
//		0,                         /* tp_alloc */
//		PySniffPacket_new,                 	/* tp_new use GenericNew*/
//};


#endif /* HARNESS_H_ */
