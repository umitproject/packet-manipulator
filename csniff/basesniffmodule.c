
#include "basesniffmodule.h"
#include "bthandler.h"
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>
#include <stdio.h>
#include <err.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <assert.h>

#include "structmember.h"

static PyTypeObject PySniffPacketType;
static void setup_PySniffPacket(PySniffPacket *self, struct frontline_packet *fp);

//General sniffing exception
PyObject *SniffError;

static PyObject *
send_debug(PyState *s, struct dbg_packet *dp, void *rp,
		       int rplen)
{
	unsigned char cp[254];
	struct hci_request rq;
	unsigned char *p = cp;
	int errnum;

	memset(&rq, 0, sizeof(rq));
	memset(cp, 0, sizeof(cp));

	/* payload descriptor */
        *p++ = FRAG_FIRST | FRAG_LAST | CHAN_DEBUG;
	memcpy(p, dp, sizeof(*dp));
	p += sizeof(*dp);

        rq.ogf    = OGF_VENDOR_CMD;
        rq.ocf    = 0x00;
        rq.event  = EVT_VENDOR;
        rq.cparam = cp;
        rq.clen   = p - cp;
        rq.rparam = rp;
        rq.rlen   = rplen;

    Py_BEGIN_ALLOW_THREADS
	errnum = hci_send_req(s->s_fd, &rq, 2000);
    Py_END_ALLOW_THREADS

    if (errnum < 0){
    	PyErr_SetString(SniffError, "hci_send_req() error");
    	return NULL;
    }

    RETURN_VOID
}

static PyObject *
send_debug_no_rp(PyState *s, struct dbg_packet *dp)
{
	unsigned char rp[254];
	return send_debug(s, dp, rp, sizeof(rp));
}

static PyObject *
populateGenPkt(PySniffPacket *pkt, void *buf, int len)
{
	PyGenericPacket *gp;
	int tmplen = len;
	uint8_t *data = (uint8_t *) buf;
	//Create L2CAP packet -- generic packet
	gp = (PyGenericPacket *)PyGenericPacketType.tp_new(&PyGenericPacketType, NULL, NULL);
	if(PyGenericPacketType.tp_init((PyObject *) gp, NULL, NULL) < 0)
	{
		PyErr_SetString(SniffError, "process_l2cap: error creating l2cap packet.");
		return NULL;
	}

	while(tmplen--) {
		if(PyList_Append((PyObject *)gp->data, PyInt_FromLong((long) *data++)) < 0)
		{
			PyErr_SetString(SniffError, "populateGenPkt: error append");
			return NULL;
		}
	}

	pkt->_payloadpkt = (PyObject *) gp;
	RETURN_VOID
}

/*
 * Returns the file descriptor (int) of the stated hci device
 */
static int get_dev_fd(char *devname)
{
	int dev, devfd;
	Py_BEGIN_ALLOW_THREADS
	dev = hci_devid(devname);
	if(dev < 0)
		errx(1, "hci_devid()");

	devfd = hci_open_dev(dev);
	if(devfd  < 0)
		errx(1, "hci_devid()2");
	Py_END_ALLOW_THREADS

	return devfd;
}

static void close_dev(int fd)
{
	Py_BEGIN_ALLOW_THREADS
	hci_close_dev(fd);
	Py_END_ALLOW_THREADS
}


/*
 * Module functions that are imported.
 * */
static PyObject *
basesniff_get_timer(PyObject *dummy, PyObject *args)
{
	unsigned char rp[254];
	char *devname ;
	struct dbg_packet pkt;
	PyState *state = NULL;

	memset(rp, 0, sizeof(rp));
	memset(&pkt, 0, sizeof(pkt));

	pkt.dp_type = CMD_TIMER;

	if(!PyArg_ParseTuple(args, "Os", &state, &devname))
			return NULL;

	//get the device fd
	state->s_fd = get_dev_fd(devname);

	send_debug(state, &pkt, rp, sizeof(rp));
	close_dev(state->s_fd);
	//return a Python integer object
	return Py_BuildValue("i", *((unsigned int *)&rp[2]));
}


static PyObject *
basesniff_set_filter(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	PyState *state;
	char *devname;
	unsigned int val;

	memset(&pkt, 0, sizeof(pkt));

	pkt.dp_type = CMD_FILTER;
	if(!PyArg_ParseTuple(args, "OsI", &state, &devname, &val))
		return NULL;

	state->s_fd = get_dev_fd(devname);

	pkt.dp_data[0] = (unsigned char) val;
	send_debug_no_rp(state, &pkt);
	close_dev(state->s_fd);

	RETURN_VOID
}


static PyObject *
basesniff_sniff_stop(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	PyState *state = NULL;
	char *devname;
	memset(&pkt, 0, sizeof(pkt));

	pkt.dp_type = CMD_STOP;
	if(! PyArg_ParseTuple(args, "Os", &state, &devname ))
		return NULL;

	state->s_fd = get_dev_fd(devname);

	send_debug_no_rp(state, &pkt);
	close_dev(state->s_fd);

	RETURN_VOID
}

//	args should consist of a PyState object, a string containing the device name
//	and 2 lists, each with 6 integers.
static PyObject *
basesniff_sniff_start(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	PyState *state;
	PyObject *master_list, *slave_list, *item;
	char *devname;
	int i;
	unsigned char peek;

	struct start_packet *sp = (struct start_packet *) &pkt.dp_data;

	memset(&pkt, 0, sizeof(pkt));
	pkt.dp_type = CMD_START;

	if(!PyArg_ParseTuple(args, "OsOO", &state, &devname,
			&master_list, &slave_list ))
		return NULL;

	state->s_fd = get_dev_fd(devname);

	if(PyList_Check(master_list) && PyList_Check(slave_list)) {

		assert(PyList_Size(master_list) == 6 && PyList_Size(slave_list) == 6);
		printf("master: ");
		for (i = 5; i >= 0; i--)
		{
			item = PyList_GetItem(master_list, 5 - i);
			if(PyInt_Check(item))
				peek = (unsigned char) PyInt_AsLong(item);
			else
				return NULL;
			sp->sp_master_rev[i] = peek;
			printf("%d ", peek);
		}
		printf("\nslave: ");
		for (i = 5; i >= 0; i--)
		{
			item = PyList_GetItem(slave_list, 5 - i);
			if(PyInt_Check(item))
				peek = (unsigned char) PyInt_AsLong(item);
			else
				return NULL;
			printf("%d ", peek);
			sp->sp_slave_rev[i] = peek;

		}
		printf("\n");
	}
	else
		return NULL;

	send_debug_no_rp(state, &pkt);
	close_dev(state->s_fd);

	RETURN_VOID
}

/* End Module Functions */

//Mark for removal soon
/*
static void hexdump(void *buf, int len)
{
	unsigned char *p = buf;

	while (len--)
		printf("%.2X ", *p++);
	printf("\n");
}
*/

static PyObject *
process_l2cap(PyState *s, void *buf, int len,
		PySniffPacket *pkt, PyObject *handler )
{
//	struct hcidump_hdr dh;
//	uint8_t type = HCI_ACLDATA_PKT;
//	hci_acl_hdr acl;
	PyGenericPacket *gp;
//	int totlen = sizeof(type) + sizeof(acl) + len;

//	printf("L2CAP: ");
//	hexdump(buf, len);
	if (s->s_dump == -1)
		RETURN_VOID

	populateGenPkt(pkt, buf, len);
	if(PyErr_Occurred())
		return NULL;

	pkt->_payloadpkt = (PyObject *)gp;

	if (! PyObject_CallMethodObjArgs(handler, PyString_FromString("recvl2cap"), pkt, NULL ))
	{
		PyErr_SetString(SniffError, "process_l2cap: recvl2cap failed");
		return NULL;
	}
/*
	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, &dh, sizeof(dh)) != sizeof(dh))
		err(1, "write()");
	if (write(s->s_dump, &type, sizeof(type)) != sizeof(type))
		err(1, "write()");
	memset(&acl, 0, sizeof(acl));
	acl.dlen	= len;
	acl.handle	= acl_handle_pack(0, s->s_llid);
	if (write(s->s_dump, &acl, sizeof(acl)) != sizeof(acl))
		err(1, "write()");

	if (write(s->s_dump, buf, len) != len)
		err(1, "write()");
	Py_END_ALLOW_THREADS
*/
	RETURN_VOID
}


/**
 * Mark for removal
 */
/*
static void dump_lmp(PyState *s, void *buf, int len)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_EVENT_PKT;
	hci_event_hdr evt;
	unsigned char csr_lmp[1+1+17+1];
	int totlen = sizeof(type) + sizeof(evt) + sizeof(csr_lmp);
	unsigned char *p = csr_lmp;

	assert(len <= 17);

	/* hcidump header
	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, &dh, sizeof(dh)) != sizeof(dh))
		err(1, "write()");

	if (write(s->s_dump, &type, sizeof(type)) != sizeof(type))
		err(1, "write()");
	Py_END_ALLOW_THREADS

	/* event header
	memset(&evt, 0, sizeof(evt));
	evt.evt		= EVT_VENDOR;
	evt.plen	= sizeof(csr_lmp);
	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, &evt, sizeof(evt)) != sizeof(evt))
		err(1, "write()");
	Py_END_ALLOW_THREADS
	/* CSRized LMP packet
	memset(csr_lmp, 0, sizeof(csr_lmp));
	*p++ = 20; /* channel ID
	*p++ = s->s_master ? 0x10 : 0x0f;
	memcpy(p, buf, len);
	p += 17;
	*p = 0; /* connection handle
	assert(((unsigned long) p - (unsigned long) csr_lmp)< sizeof(csr_lmp));
	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, csr_lmp, sizeof(csr_lmp)) != sizeof(csr_lmp))
		err(1, "write()");
	Py_END_ALLOW_THREADS
}
*/



static PyObject *
process_lmp(PyState *s, void *buf, int len,
		PySniffPacket *sniffpkt, PyObject *handler)
{
	PyLMPPacket *lmppkt;
	uint8_t *data = buf;
	int tmplen;

	//Build LMPPacket
	assert(sniffpkt != NULL);
	lmppkt = (PyLMPPacket *) PyLMPPacketType.tp_new(&PyLMPPacketType, NULL, NULL);
	if(PyLMPPacketType.tp_init((PyObject *) lmppkt, NULL, NULL) < 0)
		err(1, "Error creating PyLMPPacket.");
	assert(len <= 17); //LMP PDU should be less than or equal to 17 bytes long
	assert(lmppkt != NULL);
	sniffpkt->_payloadpkt = (PyObject *) lmppkt;

	//Populate LMPPacket
	tmplen = len;
	lmppkt->op1 = *data++;
	tmplen--;
	lmppkt->tid = lmppkt->op1 & LMP_TID_MASK;
	lmppkt->op1 >>= LMP_OP1_SHIFT;
	if(lmppkt->op1 >= 124 && lmppkt->op1 <= 127)
	{
		lmppkt->op2 = *data++;
		tmplen--;
		assert(tmplen >= 0);
	}

	while(tmplen--)
	{
		if (PyList_Append(lmppkt->payload_list, PyInt_FromLong((long) *data++)) < 0)
		{
			PyErr_SetString(SniffError, "process_lmp: Error reading payload");
			return NULL;
		}
	}

	/* run do_pin if s->s_pin */

	// Python code for callback.
	assert(handler != NULL);
	if(!PyObject_CallMethodObjArgs(handler, PyString_FromString("recvlmp"), sniffpkt, NULL))
	{
		fprintf(stderr, "process_lmp: error with callback\n");
		return PyErr_SetFromErrno(SniffError);
	}

	/* Do in callback handler as well*/
/*	if (s->s_dump != -1)
	{
		dump_lmp(s, buf, len);
	}
*/

	RETURN_VOID
}


static PyObject *
process_dv(PyState *s, void *buf, int len, PySniffPacket *sniffpkt,
		PyObject *handler)
{
	populateGenPkt(sniffpkt, buf, len);
	if(!PyObject_CallMethodObjArgs(handler, PyString_FromString("recvdv"), sniffpkt, NULL))
	{
		fprintf(stderr, "process_dv: error with callback\n");
		return PyErr_SetFromErrno(SniffError);
	}
	RETURN_VOID
}

static PyObject *
process_payload(PyState *s, void *buf, int len,
		PySniffPacket *sniffpkt, PyObject *handler)
{
	PyObject *procresult;
	switch (sniffpkt->type) {
		case TYPE_DV:
			procresult = process_dv(s, buf, len, sniffpkt, handler);
			return procresult;
	}

	if (sniffpkt->llid == LLID_LMP)
		procresult = process_lmp(s, buf, len, sniffpkt, handler);
	else
		procresult = process_l2cap(s, buf, len, sniffpkt, handler);
	return procresult;
}


static PyObject *
process_frontline(PyState *s, void *buf, int len, PyObject *handler)
{
	PySniffPacket *sniffpkt;
	struct frontline_packet *fp = buf;
	int type = (fp->fp_hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK;
	int plen = fp->fp_len >> FP_LEN_SHIFT;
	uint8_t *start = (uint8_t*) fp;
	int status = fp->fp_hdr0 & FP_ADDR_MASK;
	int i;
	int hlen = fp->fp_hlen;


	switch (hlen) {
	case HLEN_BC2:
	case HLEN_BC4:
		break;
	default:
		printf("Unknown header len %d\n", hlen);
		//abort();
		RETURN_VOID
		break;
	}
	start += hlen;


	if(PyList_Check(s->s_ignore_list))
	{
		for ( i = 0; i < PyList_Size(s->s_ignore_list); i++)
		{
			int chtype = (int) PyInt_AsLong(PyList_GetItem(s->s_ignore_list, i));
			if(chtype == type){
				 /* XXX check for appended packets */
				Py_INCREF(Py_None);
				return Py_None;
			}
		}
	}

	if (s->s_ignore_zero && plen == 0){
		Py_INCREF(Py_None);
		return Py_None;
	}

	//Create a new PySniffPacket and assign the relevant
	sniffpkt = (PySniffPacket *) PySniffPacketType.tp_new(&PySniffPacketType, NULL, NULL);
	sniffpkt->_csrpkt = fp;
	setup_PySniffPacket(sniffpkt, fp);

	/*
	s->s_llid	= (fp->fp_len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
	s->s_master	= !(fp->fp_clock & FP_SLAVE_MASK); //this must be kept
	s->s_type	= type;
	*/

/* // this can be handled in the handler
	printf("HL 0x%.2X Ch %.2d %c Clk 0x%.7X Status 0x%.1X Hdr0 0x%.2X"
	       " [type: %d addr: %d] LLID %d Len %d\n",
	       fp->fp_hlen, fp->fp_chan, s->s_master ? 'M' : 'S',
	       fp->fp_clock & FP_CLOCK_MASK,
	       fp->fp_clock >> FP_STATUS_SHIFT, fp->fp_hdr0,
	       type, status, s->s_llid, plen);
*/
	len -= hlen;
	assert(len >= 0);
	assert(len >= plen);

	if (plen) {
		printf(" ");
		if (!process_payload(s, start, plen, sniffpkt, handler))
			return NULL;
	} else {

		//Do a callback
		assert(handler != NULL);
		if(! PyObject_CallMethodObjArgs(handler, PyString_FromString("recvgenevt"), sniffpkt, NULL)){
			fprintf(stderr, "process_frontline: error with callback\n");
			return PyErr_SetFromErrno(SniffError);
		}
		printf("\n");
	}


	/* firmware seems to append fragments */
	len -= plen;
	assert(len >= 0);
	if (len)
		return process_frontline(s, start+plen, len, handler);

	RETURN_VOID
}

static PyObject *
process(PyState *state, void *buf, int len, PyObject *handler)
{
	uint8_t *type = buf;
	hci_acl_hdr *acl;
	if (*type != HCI_ACLDATA_PKT) {
		printf("Unknown type: %d\n", *type);
		Py_INCREF(Py_None);
		return Py_None;
	}

	acl = (hci_acl_hdr*) (type+1);
	assert(acl->dlen == (len - sizeof(*acl) - 1));
	return process_frontline(state, acl+1, acl->dlen, handler);
}


static PyObject *
basesniff_sniff(PyObject *self, PyObject *args, PyObject *kwds)
{
	PyState *state = NULL;
	PyObject *handler = NULL;
	char *hcidev, *dump, proceed;
	struct hci_filter flt;
	int errnum;

	char *kwlist[]= {
			"state",
			"device",
			"dump",
			"handler",
			NULL
	};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "OssO", kwlist,
			&state, &hcidev, &dump, &handler))
		return NULL;

	state->s_dump = open(dump, O_APPEND | O_WRONLY | O_CREAT, 0644);
	if(state->s_dump == -1)
	{
		PyErr_SetString(SniffError, "sniff: error opening file");
		return NULL;
	}

	state->s_fd = get_dev_fd(hcidev);

	hci_filter_clear(&flt);
	hci_filter_all_ptypes(&flt);
	hci_filter_all_events(&flt);

	Py_BEGIN_ALLOW_THREADS
	errnum = setsockopt(state->s_fd, SOL_HCI, HCI_FILTER, &flt, sizeof(flt));
	Py_END_ALLOW_THREADS

	if (errnum < 0){
		PyErr_SetString(SniffError, "sniff: can't set filter - setsockopt()");
		return NULL;
	}

	/**
	 * Ensures atomicity of assignment
	 */
	Py_BEGIN_ALLOW_THREADS
	proceed = state->s_continue;
	Py_END_ALLOW_THREADS

	//while(1){
	if(state->s_continue) {
		printf("continue =  %d\n", proceed);
	}

	while(proceed){

		Py_BEGIN_ALLOW_THREADS
		state->s_len = read(state->s_fd, state->s_buf, sizeof(state->s_buf));
		Py_END_ALLOW_THREADS

		if (state->s_len == -1)
		{
			PyErr_SetString(SniffError, "sniff: read() error");
			return NULL;
		}
		if(process(state, state->s_buf, state->s_len, handler) == NULL)
			return NULL;

	}

	printf("continue = 0\n");
	close_dev(state->s_fd);
	if(state->s_dump != -1){
		Py_BEGIN_ALLOW_THREADS
		close(state->s_dump);
		Py_END_ALLOW_THREADS
	}

	RETURN_VOID
}

/* PyState type definition */

//PyState garbage collection
static int
PyState_traverse(PyState *self, visitproc visit, void *arg)
{
	Py_VISIT(self->s_ignore_list);
	Py_VISIT(self->s_pindata);
	return 0;
}

static int
PyState_clear(PyState *self)
{
	PyObject *tmp;
	tmp = self->s_ignore_list;
	self->s_ignore_list = NULL;
	Py_XDECREF(tmp);

	tmp = self->s_pindata;
	self->s_pindata = NULL;
	Py_XDECREF(tmp);

	return 0;
}

static PyMemberDef PyState_members[] = {
		{"pinstate", T_UBYTE, offsetof(PyState, s_pin), 0, "Indicates whether pin cracking should be done"},
		{"cont_sniff", T_BYTE, offsetof(PyState, s_continue), 0, "Signals end of sniffing if false."},
		{"ignore_types", T_OBJECT_EX, offsetof(PyState, s_ignore_list), 0, "List of types to ignore"},
		{"pindata", T_OBJECT_EX, offsetof(PyState, s_pindata), 0, "Pin data (used for cracking)"},
		{"pinmaster", T_INT, offsetof(PyState, s_pin_master), 0, "Is pin master. Used in pincracking"},
		{"ignore_zero", T_INT, offsetof(PyState, s_ignore_zero), 0, "Ignore zero"},
		{NULL}
};

/*
 * This destructor does not take into account garbage collection.
 * TODO: implement garbage collection.
 */
static void
PyState_dealloc(PyState *self)
{
	PyState_clear(self);
	self->ob_type->tp_free((PyObject *) self);

}

static PyObject *
PyState_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyState *self;
	PyObject *tmp;
	unsigned char *p;
	int i;

	self = (PyState *) type->tp_alloc(type, 0);
	p = (unsigned char *) &(self->s_fd);

	if (self != NULL)
	{
		//do the equivalent of a memset 0
		while( p < (unsigned char *)self + sizeof(PyState))
			*p++ = 0;
	}

	// Restrict the type of exposed members
	self->s_ignore_list = PyList_New(0);
	if(!self->s_ignore_list)
		return NULL;

	//Populate number of slots in ignore types
	for (i = 0; i < MAX_TYPES; i++)
	{
		PyList_Append(self->s_ignore_list, PyInt_FromLong(-1));
	}

	// Set s_pindata to be a 7 by 16 two dimensional list of lists
	// This is done here to restrict the type and dimensions of s_pindata
	self->s_pindata = PyList_New(7);
	if(!self->s_pindata) return NULL;
	for(i = 0; i  < 7; i++)
	{
		tmp = PyList_GetItem(self->s_pindata, i);
		PyList_SetItem(self->s_pindata, i, PyList_New(16));
		Py_XDECREF(tmp);
	}
	self->s_pin = 0;

	return (PyObject *) self;
}

static int
PyState_init(PyState *self, PyObject  *args, PyObject *kwds)
{
	self->s_continue = 1;
	return 0;
}

static PyTypeObject PyStateType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"sniff.State",             /*tp_name*/
		sizeof(PyState),             /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor)PyState_dealloc, /*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		0,                         /*tp_repr*/
		0,                         /*tp_as_number*/
		0,                         /*tp_as_sequence*/
		0,                         /*tp_as_mapping*/
		0,                         /*tp_hash */
		0,                         /*tp_call*/
		0,                         /*tp_str*/
		0,                         /*tp_getattro*/
		0,                         /*tp_setattro*/
		0,                         /*tp_as_buffer*/
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
		"PyState object will ultimately be converted into a SniffSession. This is struct state from the original code",           /* tp_doc */
		(traverseproc)PyState_traverse,                          /* tp_traverse */
		(inquiry) PyState_clear,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,             /* tp_methods */
		PyState_members,             /* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	   (initproc)PyState_init,      /* tp_init */
		0,                         /* tp_alloc */
		PyState_new,                 /* tp_new */
};



/*
 * Definiton for PySniffPacket. Garbage collection is important for this object,
 *
 */

/**
 *  Populate the SniffPacket fields
 */
static void
setup_PySniffPacket(PySniffPacket *self, struct frontline_packet *fp)
{

	self->llid  = (fp->fp_len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
	self->bool_isFromMaster = PyBool_FromLong((long) !( fp->fp_clock & FP_SLAVE_MASK));
	self->type = (fp->fp_hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK;
	self->status = fp->fp_clock >> FP_STATUS_SHIFT;
	self->chan = fp->fp_chan;
	self->dlen = fp->fp_len >> FP_LEN_SHIFT;
	self->seq = fp->fp_seq;
	self->clock = fp->fp_clock & FP_CLOCK_MASK;
}

static int
PySniffPacket_traverse(PySniffPacket *self, visitproc visit, void *arg)
{
	Py_VISIT(self->_payloadpkt);
	return 0;
}

static int
PySniffPacket_clear(PySniffPacket *self)
{
	PyObject *tmp;
	tmp = self->_payloadpkt;
	self->_payloadpkt = NULL;
	Py_XDECREF(tmp);
	return 0;
}

static PyObject *
PySniffPacket_new(PyTypeObject *type, PyObject *args, PyObject *kwlist)
{
	PySniffPacket *self;
	self = (PySniffPacket *) type->tp_alloc(type, 0);
	if(self != NULL)
	{
		self->_csrpkt = NULL;
		Py_INCREF(Py_None);
		self->_payloadpkt = Py_None;
	}
	else
		return NULL;

	return (PyObject *)self;
}

static void
PySniffPacket_dealloc(PySniffPacket *self)
{

	PySniffPacket_clear(self);
	if(self->_csrpkt)
		free(self->_csrpkt);

	self->ob_type->tp_free((PyObject *) self);
}


static PyMemberDef PySniffPacket_members[] = {

		{"llid", T_INT, offsetof(PySniffPacket, llid), 0, "LLID."},

		{"fromMaster", T_OBJECT, offsetof(PySniffPacket, bool_isFromMaster),
				0, "Indicates if packet is sent from master device."},

		{"type", T_INT, offsetof(PySniffPacket, type), 0, "Type of packet."},

		{"clock", T_UINT, offsetof(PySniffPacket, clock), 0, "Clock."},

		// Status needs to be figured out first.
		//{"status", T_INT, offsetof(PySniffPacket, status), 0, "Status. 0 is successful."},

		{"plen", T_USHORT, offsetof(PySniffPacket, dlen), 0, "Payload length."},

		//Not useful
		//{"seq", T_UBYTE, offsetof(PySniffPacket, seq), 0, "Sequence number"},
		{"channel", T_UBYTE, offsetof(PySniffPacket, chan), 0, "Channel number."},

		{"payload", T_OBJECT, offsetof(PySniffPacket, _payloadpkt), 0, "Payload packet."},

		{NULL}

};


static PyTypeObject PySniffPacketType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"sniff.SniffPacket",        /*tp_name*/
		sizeof(PySniffPacket),      /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor)PySniffPacket_dealloc, /*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		0,                         /*tp_repr*/
		0,                         /*tp_as_number*/
		0,                         /*tp_as_sequence*/
		0,                         /*tp_as_mapping*/
		0,                         /*tp_hash */
		0,                         /*tp_call*/
		0,                         /*tp_str*/
		0,                         /*tp_getattro*/
		0,                         /*tp_setattro*/
		0,                         /*tp_as_buffer*/
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
		"PyState object will ultimately be converted into a SniffSession. This is struct state from the original code",           /* tp_doc */
		(traverseproc) PySniffPacket_traverse,                          /* tp_traverse */
		(inquiry) PySniffPacket_clear,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,             				/* tp_methods */
		PySniffPacket_members,      /* tp_members */
		0 ,     					/* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	    0,				      		/* tp_init */
		0,                         /* tp_alloc */
		PySniffPacket_new,                 	/* tp_new use GenericNew*/
};


/* Initialize the method map */
static PyMethodDef BaseSniffMethods[] =
{
		{"get_timer", (PyCFunction)basesniff_get_timer, METH_VARARGS, "gets the clock" },
		{"set_filter", (PyCFunction)basesniff_set_filter, METH_VARARGS, "sets filters. called with -f option" },
		{"stop_sniff", (PyCFunction)basesniff_sniff_stop, METH_VARARGS, "stops sniffing"},
		{"start_sniff", (PyCFunction)basesniff_sniff_start, METH_VARARGS, "starts the sniffing" },
		{"sniff", (PyCFunction)basesniff_sniff, METH_VARARGS | METH_KEYWORDS, "when sniffing is started, this prints data and dumps to file" },
		{NULL, NULL, 0, NULL}
};

/* Initialize the module */
PyMODINIT_FUNC
initsniff(void)
{
	PyObject *m;

	PySniffHandlerType.tp_new = PyType_GenericNew;
	SniffError = PyErr_NewException("sniff.SniffError", NULL, NULL);

	if(PyType_Ready(&PyStateType) < 0 ||
			PyType_Ready(&PyLMPPacketType) < 0 ||
			PyType_Ready(&PySniffPacketType) < 0 ||
			PyType_Ready(&PySniffHandlerType) < 0 ||
			PyType_Ready(&PyGenericPacketType))
		return;
	m = Py_InitModule3("sniff", BaseSniffMethods, "Main sniffing module");

	if( m == NULL)
		return;

	Py_INCREF(&PyStateType);
	Py_INCREF(&PyLMPPacketType);
	Py_INCREF(&PyGenericPacketType);
	Py_INCREF(&PySniffPacketType);
	Py_INCREF(&PySniffHandlerType);
	Py_INCREF(SniffError);

	PyModule_AddObject(m, "State", (PyObject *)&PyStateType);
	PyModule_AddObject(m, "_LMPPacket", (PyObject *) &PyLMPPacketType);
	PyModule_AddObject(m, "_GenericPacket", (PyObject *) &PyGenericPacketType);
	PyModule_AddObject(m, "SniffPacket", (PyObject *)&PySniffPacketType);
	PyModule_AddObject(m, "SniffHandler", (PyObject *) &PySniffHandlerType);
	PyModule_AddObject(m, "SniffError", SniffError);

	PyModule_AddIntMacro(m, HCI_EVENT_PKT);
	PyModule_AddIntMacro(m, HCI_ACLDATA_PKT);
	PyModule_AddIntMacro(m, HCI_COMMAND_PKT);
	PyModule_AddIntMacro(m, HCI_SCODATA_PKT);
	PyModule_AddIntMacro(m, HCI_VENDOR_PKT);

}
