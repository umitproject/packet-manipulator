
#include "basesniffmodule.h"
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

/* Actual port of the methods */
static void send_debug(PyState *s, struct dbg_packet *dp, void *rp,
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

    if (errnum < 0) err(1, "hci_send_req()");
}

static void send_debug_no_rp(PyState *s, struct dbg_packet *dp)
{
	unsigned char rp[254];

	send_debug(s, dp, rp, sizeof(rp));
}

/*
 * Returns the file descriptor (int) of the stated hci device
 */
static int get_dev_fd(char *devname)
{
	int dev, devfd;
	Py_BEGIN_ALLOW_THREADS
	dev = hci_devid(devname);
	if(dev < 0) errx(1, "hci_devid()");

	devfd = hci_open_dev(dev);
	if(devfd  < 0) errx(1, "hci_devid()2");
	Py_END_ALLOW_THREADS

	printf("dev fd = %d\n", devfd);
	return devfd;
}

static void close_dev(int fd)
{
	Py_BEGIN_ALLOW_THREADS
	hci_close_dev(fd);
	Py_END_ALLOW_THREADS
}

/* External functions
 * All external functions should call a
 *
 * */
static PyObject *
basesniff_get_timer(PyObject *self, PyObject *args)
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

	printf("Filter packets: %d\n", (unsigned char)val);
	state->s_fd = get_dev_fd(devname);

	pkt.dp_data[0] = (unsigned char) val;
	send_debug_no_rp(state, &pkt);
	close_dev(state->s_fd);

	Py_INCREF(Py_None);
	return Py_None;
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

	Py_INCREF(Py_None);
	return Py_None;

}

//args should consist of a PyState object and 2 lists, each with 6 integers.
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
	Py_INCREF(Py_None);
	return Py_None;
}

/* End External Functions */


static void hexdump(void *buf, int len)
{
	unsigned char *p = buf;

	while (len--)
		printf("%.2X ", *p++);
	printf("\n");
}

static void process_l2cap(PyState *s, void *buf, int len)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_ACLDATA_PKT;
	hci_acl_hdr acl;
	int totlen = sizeof(type) + sizeof(acl) + len;

	printf("L2CAP: ");
	hexdump(buf, len);

	if (s->s_dump == -1)
		return;

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
}


static void dump_lmp(PyState *s, void *buf, int len)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_EVENT_PKT;
	hci_event_hdr evt;
	unsigned char csr_lmp[1+1+17+1];
	int totlen = sizeof(type) + sizeof(evt) + sizeof(csr_lmp);
	unsigned char *p = csr_lmp;

	assert(len <= 17);

	/* hcidump header */
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

	/* event header */
	memset(&evt, 0, sizeof(evt));
	evt.evt		= EVT_VENDOR;
	evt.plen	= sizeof(csr_lmp);
	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, &evt, sizeof(evt)) != sizeof(evt))
		err(1, "write()");
	Py_END_ALLOW_THREADS
	/* CSRized LMP packet */
	memset(csr_lmp, 0, sizeof(csr_lmp));
	*p++ = 20; /* channel ID */
	*p++ = s->s_master ? 0x10 : 0x0f;
	memcpy(p, buf, len);
	p += 17;
	*p = 0; /* connection handle */
	assert(((unsigned long) p - (unsigned long) csr_lmp)< sizeof(csr_lmp));
	Py_BEGIN_ALLOW_THREADS
	if (write(s->s_dump, csr_lmp, sizeof(csr_lmp)) != sizeof(csr_lmp))
		err(1, "write()");
	Py_END_ALLOW_THREADS
}


/*
 * For pin-cracking
 *
 */
#define GOT_IN_RAND	(1 << 1)
#define GOT_COMB1	(1 << 2)
#define GOT_COMB2	(1 << 3)
#define GOT_AU_RAND1	(1 << 4)
#define GOT_SRES1	(1 << 5)
#define GOT_AU_RAND2	(1 << 6)
#define GOT_SRES2	(1 << 7)
static void do_pin(PyState *s, int op, void *buf, int len)
{
	int i, j;

	switch (op) {
	case LMP_IN_RAND:
		s->s_pin = 1 | GOT_IN_RAND;
		s->s_pin_master = s->s_master;
		memcpy(s->s_pin_data[0], buf, len);
		break;

	case LMP_COMB_KEY:
		if (!(s->s_pin & GOT_IN_RAND))
			return;

		if (s->s_master == s->s_pin_master) {
			memcpy(s->s_pin_data[1], buf, len);
			s->s_pin |= GOT_COMB1;
		} else {
			memcpy(s->s_pin_data[2], buf, len);
			s->s_pin |= GOT_COMB2;
		}
		break;

	case LMP_AU_RAND:
		if ((!(s->s_pin & GOT_COMB1))
		    || (!(s->s_pin & GOT_COMB2)))
			return;

		if (s->s_master == s->s_pin_master) {
			memcpy(s->s_pin_data[3], buf, len);
			s->s_pin |= GOT_AU_RAND1;
		} else {
			memcpy(s->s_pin_data[4], buf, len);
			s->s_pin |= GOT_AU_RAND2;
		}
		break;

	case LMP_SRES:
		if (s->s_master != s->s_pin_master) {
			if (!(s->s_pin & GOT_AU_RAND1))
				return;
			memcpy(s->s_pin_data[6], buf, len);
			s->s_pin |= GOT_SRES1;
		} else {
			if (!(s->s_pin & GOT_AU_RAND2))
				return;
			memcpy(s->s_pin_data[5], buf, len);
			s->s_pin |= GOT_SRES2;
		}
		break;

	default:
		return;
	}

	if (s->s_pin != 0xFF)
		return;

	printf("btpincrack Go ");
	if (s->s_pin_master)
		printf("<master> <slave> ");
	else
		printf("<slave> <master> ");

	for (i = 0;  i < 7; i++) {
		int len = i >= 5 ? 4 : 16;

		for (j = 0; j < len; j++)
			printf("%.2x", s->s_pin_data[i][j]);

		printf(" ");
	}
	printf("\n");
	s->s_pin = 1;
}



static void process_lmp(PyState *s, void *buf, int len)
{
	uint8_t *data = buf;
	int op1, op2 = -1;
	int tid;


	if (s->s_dump != -1)
		dump_lmp(s, buf, len);

	op1 = *data++;
	len--;
	assert(len >= 0);
	tid = op1 & LMP_TID_MASK;
	op1 >>= LMP_OP1_SHIFT;

	if (op1 >= 124 && op1 <= 127) {
		op2 = *data++;
		len--;
		assert(len >= 0);
	}

	printf("LMP Tid %d Op1 %d", tid, op1);
	if (op2 != -1)
		printf(" Op2 %d", op2);

	printf(": ");
	hexdump(data, len);

	if (s->s_pin)
		do_pin(s, op1, data, len);
}


static void process_dv(PyState *s, void *buf, int len)
{
	printf("DV: ");
	hexdump(buf, len);
}

static void process_payload(PyState *s, void *buf, int len)
{
	switch (s->s_type) {
	case TYPE_DV:
		process_dv(s, buf, len);
		return;
	}

	if (s->s_llid == LLID_LMP)
		process_lmp(s, buf, len);
	else
		process_l2cap(s, buf, len);
}

static void
process_frontline(PyState *s, void *buf, int len)
{
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
		abort();
		break;
	}
	start += hlen;

//	for (i = 0; i < MAX_TYPES; i++) {
//		if (s->s_ignore[i] == type)
//			return; /* XXX check for appended packets */
//	}

	if(PyList_Check(s->s_ignore_list))
	{
		for ( i = 0; i < PyList_Size(s->s_ignore_list); i++)
		{
			int chtype = (int) PyInt_AsLong(PyList_GetItem(s->s_ignore_list, i));
			if(chtype == type)
				return; /* XXX check for appended packets */
		}
	}

	if (s->s_ignore_zero && plen == 0)
		return;

	s->s_llid	= (fp->fp_len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
	s->s_master	= !(fp->fp_clock & FP_SLAVE_MASK);
	s->s_type	= type;
	printf("HL 0x%.2X Ch %.2d %c Clk 0x%.7X Status 0x%.1X Hdr0 0x%.2X"
	       " [type: %d addr: %d] LLID %d Len %d",
	       fp->fp_hlen, fp->fp_chan, s->s_master ? 'M' : 'S',
	       fp->fp_clock & FP_CLOCK_MASK,
	       fp->fp_clock >> FP_STATUS_SHIFT, fp->fp_hdr0,
	       type, status, s->s_llid, plen);

	len -= hlen;
	assert(len >= 0);
	assert(len >= plen);

	if (plen) {
		printf(" ");
		process_payload(s, start, plen);
	} else
		printf("\n");

	/* firmware seems to append fragments */
	len -= plen;
	assert(len >= 0);
	if (len)
		process_frontline(s, start+plen, len);
}

static void
process(PyState *state, void *buf, int len)
{
	uint8_t *type = buf;
	hci_acl_hdr *acl;
	if (*type != HCI_ACLDATA_PKT) {
		printf("Unknown type: %d\n", *type);
		return;
	}

	acl = (hci_acl_hdr*) (type+1);
	assert(acl->dlen == (len - sizeof(*acl) - 1));
	process_frontline(state, acl+1, acl->dlen);

}


// Main function:
// Take note, we change this to include the string representation of the device
// as one of the parameters(checked)
static PyObject *
basesniff_sniff(PyObject *self, PyObject *args, PyObject *kwds)
{
	PyState *state = NULL;
	char *hcidev, *dump;
	struct hci_filter flt;
	int errnum;

	char *kwlist[]= {
			"state",
			"device",
			"dump",
			NULL
	};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "Oss", kwlist,
			&state, &hcidev, &dump))
		return NULL;
	printf("sniff called! dump =  %s, hcidev = %s\n", dump, hcidev);
	//Open device, find out more about exceptions here

	state->s_dump = open(dump, O_APPEND | O_WRONLY | O_CREAT, 0644);
	state->s_fd = get_dev_fd(hcidev);

	hci_filter_clear(&flt);
	hci_filter_all_ptypes(&flt);
	hci_filter_all_events(&flt);

	Py_BEGIN_ALLOW_THREADS
	errnum = setsockopt(state->s_fd, SOL_HCI, HCI_FILTER, &flt, sizeof(flt));
	Py_END_ALLOW_THREADS

	if (errnum < 0){
		errx(1, "Can't set filter - setsockopt()");
	}

	while(1){

		//blocking calls need to be sandwiched with this. If I remember correctly.
		printf("read\n");
		Py_BEGIN_ALLOW_THREADS
		state->s_len = read(state->s_fd, state->s_buf, sizeof(state->s_buf));
		Py_END_ALLOW_THREADS
		if (state->s_len == -1)
			err(1, "read()");
		process(state, state->s_buf, state->s_len);
	}

	close_dev(state->s_fd);
	if(state->s_dump != -1){
		Py_BEGIN_ALLOW_THREADS
		close(state->s_dump);
		Py_END_ALLOW_THREADS
	}
	// C Idiom for returning type void
	Py_INCREF(Py_None);
	return Py_None;
}

/* PyState type definition */

static PyMemberDef PyState_members[] = {
		{"ignore_types", T_OBJECT_EX, offsetof(PyState, s_ignore_list), 0, "List of types to ignore"},
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
	Py_XDECREF(self->s_ignore_list);
	self->ob_type->tp_free((PyObject *) self);

}

static PyObject *
PyState_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyState *self;
	unsigned char *p;

	self = (PyState *) type->tp_alloc(type, 0);
	p = (unsigned char *) &(self->s_fd);

	if (self != NULL)
	{
		//do the equivalent of a memset 0
		while( p < (unsigned char *)self + sizeof(PyState))
			*p++ = 0;
	}
	return (PyObject *) self;
}

static int
PyState_init(PyState *self, PyObject  *args, PyObject *kwds)
{
	self->s_ignore_list = PyList_New(0);
	if(!self->s_ignore_list)
		return -1;
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
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
		"PyState object will ultimately be converted into a SniffSession. This is struct state from the original code",           /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
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
	if(PyType_Ready(&PyStateType) < 0)
		return;
	m = Py_InitModule("sniff", BaseSniffMethods);
	Py_INCREF(&PyStateType);
	PyModule_AddObject(m, "State", (PyObject *)&PyStateType);

}
