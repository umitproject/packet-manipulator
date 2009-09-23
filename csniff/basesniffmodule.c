

#include <stdio.h>
#include <err.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/socket.h>
#include <sys/ioctl.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>


#include "basesniffmodule.h"
#include "btconstants.h"
#include "layers.h"
#include "bthandler.h"
#include "structmember.h"

#ifdef DEBUG

#include "harness.h"

#endif


//General sniffing exception
PyObject *SniffError;

static PyObject *EMPTY_TUPLE;
static PyObject *EMPTY_DICT;
static PyTypeObject PyHCIDeviceType;


static PyObject *
send_debug(int socket_fd, struct dbg_packet *dp, void *rp,
		       int rplen)
{
	unsigned char cp[254];
	struct hci_request rq;
	unsigned char *p = cp;
	int errnum;


	Py_BEGIN_ALLOW_THREADS
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


	errnum = hci_send_req(socket_fd, &rq, 2000);
    Py_END_ALLOW_THREADS

    if (errnum < 0){
    	PyErr_SetString(SniffError, "hci_send_req() error");
    	return NULL;
    }

    RETURN_VOID
}

static PyObject *
send_debug_no_rp(int socket_fd, struct dbg_packet *dp)
{
	unsigned char rp[254];
	return send_debug(socket_fd, dp, rp, sizeof(rp));
}

/**
 * getctl, get_dev_list
 * Functions for getting of list of HCI devices connected. With code adapted from
 * the BlueZ hciconfig tool
 */

static int getctl(void)  {

	int ctl = -1;
	if ((ctl = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)) < 0){

		perror("Can't open HCI socket");
		return -1;
	}
	return ctl;
}


static struct hci_dev_info *di;
static int di_num;

static void get_dev_list(int ctl)  {

	struct hci_dev_list_req *dl;
	struct hci_dev_info *ptmp;
	struct hci_dev_req *dr;
	int num = 0, i = 0;


	di = (struct hci_dev_info *) malloc(HCI_MAX_DEV * sizeof(struct hci_dev_info));
	memset(di, 0, HCI_MAX_DEV);
	ptmp = di;

	if (!(dl = malloc(HCI_MAX_DEV * sizeof(struct hci_dev_req) + sizeof(uint16_t)))) {
		perror("Can't allocate memory");
		return;
	}

	dl->dev_num = HCI_MAX_DEV;
	dr = dl->dev_req;

	if(ioctl(ctl, HCIGETDEVLIST, (void *) dl) < 0) {
		perror("Can't get device list");
		return;
	}

	for (i = 0; i < dl->dev_num; i++)  {
		ptmp->dev_id = (dr+i)->dev_id;
		if(ioctl(ctl, HCIGETDEVINFO, (void *) ptmp) < 0)
			continue;
		num++;
		if(hci_test_bit(HCI_RAW, &ptmp->flags) &&
				!bacmp(&ptmp->bdaddr, BDADDR_ANY)) {
			int dd = hci_open_dev(ptmp->dev_id);
			hci_read_bd_addr(dd, &ptmp->bdaddr, 1000);
			hci_close_dev(dd);
		}
		ptmp++;
	}

	di_num = num;
}

static PyObject *
basesniff_getdevlist(PyObject *dummy)
{
	PyObject *retlist = PyList_New(0);
	PyHCIDevice *tmpdev = NULL;
	struct hci_dev_info *tmpDi;

	int ctl = -1, i = 0, namelen = 0;
	if((ctl = getctl()) < 0)
	{
		err(1, "Error getting ctl");
		return NULL;
	}


	get_dev_list(ctl);
	printf("Number of devices detected = %d\n", di_num);

	tmpDi = di;
	for (; i < di_num; i++)
	{

		tmpdev = (PyHCIDevice *) PyHCIDeviceType.tp_new(&PyHCIDeviceType, EMPTY_TUPLE, EMPTY_DICT);
		if ( PyHCIDeviceType.tp_init((PyObject *)tmpdev, EMPTY_TUPLE, EMPTY_DICT) < 0) {
			err(1, "Error initializing HCIDevice");
			return NULL;
		}

		//Allocate memory for ba2str string
		//tmpdev->dev.name = tmpDi->name;
		namelen = strlen(tmpDi->name);
		tmpdev->dev.name = (char *) calloc(namelen, sizeof(char));
		memcpy(tmpdev->dev.name, tmpDi->name, namelen );

		tmpdev->dev.bt_add = (char *) malloc(19 * sizeof(char));
		ba2str(&tmpDi->bdaddr, tmpdev->dev.bt_add);
		tmpdev->devid = tmpDi->dev_id;

		//Append to list
		PyList_Append(retlist, (PyObject *) tmpdev);
		tmpDi++;
	}

	//Free di to prevent memory leak
	free(di);
	return retlist;
}

/**
 *
 *	Utility functions for creation of SniffUnits
 *
 */
static PyObject *
set_unit_payload(PyLayerUnit *raw, void *buf, int len)
{
	PyRawObject *payload;
	int tmplen = len;
	uint8_t *data = (uint8_t *) buf;

	payload = (PyRawObject *) PyRawObjectType.tp_new(&PyRawObjectType, NULL, NULL);
	if(PyRawObjectType.tp_init((PyObject *) payload, NULL, NULL) < 0)
	{
		PyErr_SetString(SniffError, "set_unit_payload: error creating payload.");
		return NULL;
	}

	while(tmplen--){
		if(PyList_Append((PyObject *)payload->rawdata, PyInt_FromLong((long) *data++)) < 0)
		{
			PyErr_SetString(SniffError, "set_unit_payload: error append");
			return NULL;
		}
	}

	raw->payload = payload;
	RETURN_VOID
}

static void
set_sniffhdr_fields(PySniffHdr *hdr, struct frontline_packet *fp)
{
	memcpy(&hdr->hlen, fp, sizeof(struct frontline_packet));

}

static int
get_sniffraw_type(PySniffUnit *sniffraw)
{
	PySniffHdr *hdr = (PySniffHdr *)sniffraw->raw.hdr;
	return (hdr->hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK;
}

static int
get_sniffraw_llid(PySniffUnit *sniffraw)
{
	return (((PySniffHdr *) sniffraw->raw.hdr)->dlen >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
}

/*
 * Returns the file descriptor (int) of the specified hci device
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
 * ****************************
 * Exposed module functions.  *
 *                            *
 * ****************************/


static PyObject *
basesniff_close_hcidev(PyObject *dummy, PyObject *args)
{
	PyHCIDevice *dev;

	if (! PyArg_ParseTuple(args, "O", (PyObject *)&dev)
			|| ! PyObject_HasAttrString((PyObject *)dev, "hcidevid")) {
		return NULL;
	}
	close_dev((int)dev->devid);
	RETURN_VOID
}

/*
 * @return HCIDevice instance
 */
static PyObject *
basesniff_open_hcidev(PyObject *dummy, PyObject *args)
{
	char *devname = NULL;
	int devid, namelen;
	PyHCIDevice *dev;

	if (!PyArg_ParseTuple(args, "s", &devname))
		return NULL;

	devid = get_dev_fd(devname);

	dev = (PyHCIDevice *)PyHCIDeviceType.tp_new(&PyHCIDeviceType, args, EMPTY_DICT);
	if (PyHCIDeviceType.tp_init((PyObject *)dev, args, EMPTY_DICT) < 0)
		return NULL;

	Py_BEGIN_ALLOW_THREADS

	dev->devid = (uint16_t) devid;
	namelen = strlen(devname);
	dev->dev.name = (char *) calloc(namelen, sizeof(char));
	memcpy(dev->dev.name, devname, namelen);

	Py_END_ALLOW_THREADS

	return (PyObject *)dev;
}


/**
 * @param state PyState object
 * @param devname Device name.
 * @return Timer vaue as Python integer.
 */
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

	send_debug(state->s_fd, &pkt, rp, sizeof(rp));
	close_dev(state->s_fd);
	//return a Python integer object
	return Py_BuildValue("i", *((unsigned int *)&rp[2]));
}


static PyObject *
basesniff_set_filter(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	char *devname;
	unsigned int val;
	int sniff_fd;

	memset(&pkt, 0, sizeof(pkt));

	pkt.dp_type = CMD_FILTER;
	if(!PyArg_ParseTuple(args, "sI", &devname, &val))
		return NULL;

	sniff_fd = get_dev_fd(devname);

	pkt.dp_data[0] = (unsigned char) val;
	send_debug_no_rp(sniff_fd, &pkt);
	close_dev(sniff_fd);

	RETURN_VOID
}

/*
 * @param devname The name of the sniffing device (e.g. hci0)
 */
static PyObject *
basesniff_sniff_stop(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	char *devname;
	int sniff_fd;
	memset(&pkt, 0, sizeof(pkt));

	pkt.dp_type = CMD_STOP;
	if(! PyArg_ParseTuple(args, "s", &devname ))
		return NULL;

	sniff_fd = get_dev_fd(devname);
	send_debug_no_rp(sniff_fd, &pkt);
	close_dev(sniff_fd);

	RETURN_VOID
}


/**
 * @param state 		PyState object
 * @param devname 		Name of the device (e.g. hci0)
 * @param master_list	List of 6 integers representing the Bluetooth address
 * 						of the master device.
 * @param slave_list	List of 6 integers representing the Bluetooth address
 * 						of the slave device.
 */
static PyObject *
basesniff_sniff_start(PyObject *dummy, PyObject *args)
{
	struct dbg_packet pkt;
	PyState *state;
	PyObject *master_list, *slave_list, *item;
	char *devname;
	int i, sniff_fd;
	unsigned char peek;
	struct start_packet *sp;

	Py_BEGIN_ALLOW_THREADS
	sp = (struct start_packet *) &pkt.dp_data;
	memset(&pkt, 0, sizeof(pkt));
	pkt.dp_type = CMD_START;
	Py_END_ALLOW_THREADS

	if(!PyArg_ParseTuple(args, "OsOO", &state, &devname,
			&master_list, &slave_list ))
		return NULL;

	sniff_fd = get_dev_fd(devname);

	Py_BEGIN_ALLOW_THREADS
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
	Py_END_ALLOW_THREADS

	send_debug_no_rp(sniff_fd, &pkt);
	close_dev(sniff_fd);

	RETURN_VOID
}

/* End Module Functions */

static PyObject *
process_l2cap(PyState *s, void *buf, int len,
		PySniffUnit *pkt, PyObject *handler )
{
	uint16_t *hdr = buf, hlen = 0, chanid = 0;
	int tmplen = len, field_len = sizeof(uint16_t);
	PyL2CAPHdr *l2caphdr;
	PyL2CAP *l2cap;

#ifdef DEBUG
	printf("L2CAP: ");
	hexdump(buf, len);
	dump_l2cap(s->s_dump, buf, len);
#endif

	//set_unit_payload(&pkt->raw, buf, len);
	hlen = *hdr;
	tmplen -= field_len;
	hdr += field_len;
	chanid = *hdr;
	tmplen -= field_len;
	hdr += field_len;

	assert(tmplen >= 0);

	l2caphdr = (PyL2CAPHdr *) PyL2CAPHdrType.tp_new(&PyL2CAPHdrType, NULL, NULL);
	if (PyL2CAPHdrType.tp_init((PyObject *) l2caphdr, EMPTY_TUPLE, EMPTY_DICT) < 0)
		err(1, "Error creating L2CAPHdr");

	l2cap = (PyL2CAP *) PyLayerUnitType.tp_new(&PyLayerUnitType, NULL, NULL);
	if(PyLayerUnitType.tp_init((PyObject *)l2cap, EMPTY_TUPLE, EMPTY_DICT) < 0)
		return NULL;

	l2caphdr->chan_id = chanid;
	l2caphdr->length = hlen;
	l2cap->hdr = (PyLayerHeader *) l2caphdr;
	set_unit_payload(l2cap, hdr, tmplen);

	pkt->raw.payload = (PyRawObject *) l2cap;

	if(PyErr_Occurred())
		return NULL;

	if (! PyObject_CallMethodObjArgs(handler, PyString_FromString("recvl2cap"), pkt, NULL ))
	{
		PyErr_SetString(SniffError, "process_l2cap: recvl2cap failed");
		return NULL;
	}
	RETURN_VOID
}

static PyObject *
process_lmp(PyState *s, void *buf, int len,
		PySniffUnit *sniffpkt, PyObject *handler)
{

	PyLMP *lmp;
	PyLMPHdr *hdr;
	uint8_t *data = buf, op1, tid;
	int tmplen;

	//Build LMPPacket
	assert(sniffpkt != NULL);

	//////////////// Step 1. Build the LMPHeader /////////////////////
	hdr = (PyLMPHdr *) PyLMPHdrType.tp_new(&PyLMPHdrType, NULL, NULL);
	if(PyLMPHdrType.tp_init((PyObject *) hdr, EMPTY_TUPLE, EMPTY_DICT) < 0) //Possible errors here
		err(1, "Error creating LMPHdr"); //TODO: Formal error indication?

	/////////// LMP PDU should be less than or equal to 17 bytes long
	assert(len <= 17);

	lmp = (PyLMP *) PyLayerUnitType.tp_new(&PyLayerUnitType, NULL, NULL);
	if(PyLayerUnitType.tp_init((PyObject *)lmp, EMPTY_TUPLE, EMPTY_DICT) < 0)
		return NULL;

	lmp->hdr = (PyLayerHeader *) hdr;

	tmplen = len;
	op1 = *data++;
	tmplen--;
	tid = op1 & LMP_TID_MASK;
	((PyLMPHdr *) lmp->hdr)->tid = tid;
	op1 =  op1 >> LMP_OP1_SHIFT;
	if(op1 >= 124 && op1 <= 127)
	{
		((PyLMPHdr *)lmp->hdr)->op2 = *data++;
		tmplen--;
		assert(tmplen >= 0);
	}
	((PyLMPHdr *) lmp->hdr)->op1 = op1;

	////////////////////// Step 2. Populate LMP payload ///////////////////////
	if(set_unit_payload(lmp, data, tmplen) == NULL)
		return NULL;

	//////////////////// Step 3. Set LMP as SniffUnit payload ////////////////
	sniffpkt->raw.payload= (PyRawObject *)lmp;

#ifdef DEBUG

	//Place the debug code before the handler code
	//because the bugs may occur in the handler

	hexdump(buf, len);
	if (s->s_dump != -1)
	{
		dump_lmp(s->s_dump, s->s_master, buf, len);
	}
#endif

	// Python code for callback.
	assert(handler != NULL);
	if(!PyObject_CallMethodObjArgs(handler, PyString_FromString("recvlmp"), sniffpkt, NULL))
	{
		fprintf(stderr, "process_lmp: error with callback\n");
		return PyErr_SetFromErrno(SniffError);
	}

	RETURN_VOID
}


static PyObject *
process_dv(PyState *s, void *buf, int len, PySniffUnit *sniffpkt,
		PyObject *handler)
{
	if(!set_unit_payload(&sniffpkt->raw, buf, len))
		return NULL;

	if(!PyObject_CallMethodObjArgs(handler, PyString_FromString("recvdv"), sniffpkt, NULL))
	{
		fprintf(stderr, "process_dv: error with callback\n");
		return PyErr_SetFromErrno(SniffError);
	}
	RETURN_VOID
}

static PyObject *
process_payload(PyState *s, void *buf, int len,
		PySniffUnit *sniffpkt, PyObject *handler)
{
	PyObject *procresult;
	switch (get_sniffraw_type(sniffpkt)) {
		case TYPE_DV:
			procresult = process_dv(s, buf, len, sniffpkt, handler);
			return procresult;
	}

	if (get_sniffraw_llid(sniffpkt) == LLID_LMP)
		procresult = process_lmp(s, buf, len, sniffpkt, handler);
	else
		procresult = process_l2cap(s, buf, len, sniffpkt, handler);
	return procresult;
}


static PyObject *
process_frontline(PyState *s, void *buf, int len, PyObject *handler)
{
	PySniffUnit *sniffunit;
	PySniffHdr *hdr;
	struct frontline_packet *fp = buf;
	int plen = fp->fp_len >> FP_LEN_SHIFT;
	uint8_t *start = (uint8_t*) fp;
	int hlen = fp->fp_hlen, i;
	int type = (fp->fp_hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK;

#ifdef DEBUG
	int status = fp->fp_hdr0 & FP_ADDR_MASK;
#endif

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
	hdr = (PySniffHdr *) PySniffHdrType.tp_new(&PySniffHdrType, NULL, NULL);
	if(PySniffHdrType.tp_init((PyObject *)hdr, EMPTY_TUPLE, EMPTY_DICT) < 0)
		return NULL;

	set_sniffhdr_fields(hdr, fp);

#ifdef DEBUG
	print_sniff_hdr(hdr, fp);
#endif

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

	sniffunit = (PySniffUnit *) PySniffRawType.tp_new(&PySniffRawType, NULL, NULL);
	if(PySniffRawType.tp_init((PyObject *)sniffunit, EMPTY_TUPLE, EMPTY_DICT) < 0)
			return NULL;

	sniffunit->raw.hdr = (PyLayerHeader *) hdr;

#ifdef DEBUG

	//For comparison of printouts with the Python implementation
	s->s_llid	= (fp->fp_len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK;
	s->s_master	= !(fp->fp_clock & FP_SLAVE_MASK); //this must be kept
	s->s_type	= type;


	printf("HL 0x%.2X Ch %.2d %c Clk 0x%.7X Status 0x%.1X Hdr0 0x%.2X"
	       " [type: %d addr: %d] LLID %d Len %d\n",
	       fp->fp_hlen, fp->fp_chan, s->s_master ? 'M' : 'S',
	       fp->fp_clock & FP_CLOCK_MASK,
	       fp->fp_clock >> FP_STATUS_SHIFT, fp->fp_hdr0,
	       type, status, s->s_llid, plen);
#endif

	len -= hlen;
	assert(len >= 0);
	assert(len >= plen);

	if (plen) {
#ifdef DEBUG
		//For debug output formatting
		printf(" ");
#endif
		if (!process_payload(s, start, plen, sniffunit, handler))
			return NULL;
	} else {

		//Do a callback
		assert(handler != NULL);
		if(! PyObject_CallMethodObjArgs(handler, PyString_FromString("recvgenevt"), sniffunit, NULL)){
			fprintf(stderr, "process_frontline: error with callback\n");
			return PyErr_SetFromErrno(SniffError);
		}
#ifdef DEBUG
		//For debug output formatting
		printf("\n");
#endif
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
	PyObject *resume = Py_True;
	char *hcidev, *dump;
	struct hci_filter flt;
	int errnum, len, fd;

	char *kwlist[]= {
			"state",
			"device",
			"handler",
			NULL
	};


	if (!PyArg_ParseTupleAndKeywords(args, kwds, "OsO", kwlist,
			&state, &hcidev, &handler))
		return NULL;

//	state->s_dump = open(dump, O_APPEND | O_WRONLY | O_CREAT, 0644);
//	if(state->s_dump == -1)
//	{
//		PyErr_SetString(SniffError, "sniff: error opening file");
//		return NULL;
//	}

	printf("hcidev to open: %s\n", hcidev);
	fd = get_dev_fd(hcidev);

	Py_BEGIN_ALLOW_THREADS
	hci_filter_clear(&flt);
	hci_filter_all_ptypes(&flt);
	hci_filter_all_events(&flt);

	errnum = setsockopt(fd, SOL_HCI, HCI_FILTER, &flt, sizeof(flt));
	Py_END_ALLOW_THREADS

	if (errnum < 0){
		PyErr_SetString(SniffError, "sniff: can't set filter - setsockopt()");
		return NULL;
	}

	while(resume == Py_True){

		Py_BEGIN_ALLOW_THREADS
		len = read(fd, state->s_buf, sizeof(state->s_buf));
		Py_END_ALLOW_THREADS
		if (len == -1)
		{
			PyErr_SetString(SniffError, "sniff: read() error");
			return NULL;
		}

		//Hopefully there's enough time slices apportioned
		//in process and its sub-calls to allow for changes
		//in resume
		if(process(state, state->s_buf, len, handler) == NULL)
			return NULL;
		resume = state->bool_resume;

		//Mark for deletion
		Py_BEGIN_ALLOW_THREADS

//		if(resume == Py_False)
//			printf("Yes! we detect a change");

		Py_END_ALLOW_THREADS
	}

	close_dev(fd);

	RETURN_VOID
}

/* PyState type definition */

//PyState garbage collection
static int
PyState_traverse(PyState *self, visitproc visit, void *arg)
{
	Py_VISIT(self->s_ignore_list);
	Py_VISIT(self->s_pindata);
	Py_VISIT(self->bool_resume);
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

	tmp = self->bool_resume;
	self->bool_resume = NULL;
	Py_XDECREF(tmp);

	return 0;
}

static PyMemberDef PyState_members[] = {
		{"pinstate", T_UBYTE, offsetof(PyState, s_pin), 0,
				"Indicates whether pin cracking should be done"},
		{"resume_sniff", T_OBJECT, offsetof(PyState, bool_resume), 0,
				"Controls state of sniffing. \
						True to resume, false otherwise"},
		{"ignore_types", T_OBJECT_EX, offsetof(PyState, s_ignore_list), 0,
				"List of types to ignore"},
		{"pindata", T_OBJECT_EX, offsetof(PyState, s_pindata), 0,
				"Pin data (used for cracking)"},
		{"pinmaster", T_OBJECT, offsetof(PyState, s_pin_master), 0,
				"Is pin master. Boolean object. Used in pincracking"},
		{"ignore_zero", T_INT, offsetof(PyState, s_ignore_zero), 0,
				"Ignore zero"},
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

	self->bool_resume = Py_True;
	self->s_pin_master = Py_False;
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
		"btsniff.CaptureState",             /*tp_name*/
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


/**
 * Abstractions for Bluetooth devices
 */

static int
PyBtDevice_init(PyBtDevice *self, PyObject *args, PyObject *kwds)
{
	char *name = "", *add="";
	char *kwlist[] =  {
			"name",
			"add",
			NULL
	};

	if (! PyArg_ParseTupleAndKeywords(args, kwds, "|ss", kwlist, &name, &add ))
	{
		return -1;
	}

	self->name  = name;
	self->bt_add = add;
	return 0;
}

static void
PyBtDevice_dealloc(PyBtDevice *self)
{
	return;
}

static PyMemberDef PyBtDevice_members[] =  {
		{"name", T_STRING, offsetof(PyBtDevice, name), 0,
				"Name of the device"},
		{"btadd", T_STRING, offsetof(PyBtDevice, bt_add), 0,
				"Bluetooth adress of the device"},
		{ NULL }
};

static PyTypeObject PyBtDeviceType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btsniff.BtDevice",             /*tp_name*/
		sizeof(PyBtDevice),             /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor)PyBtDevice_dealloc, /*tp_dealloc*/
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
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE , /*tp_flags*/
		"Abstraction for a Bluetooth device",      /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,             /* tp_methods */
		PyBtDevice_members,             /* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	   (initproc)PyBtDevice_init,      /* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};


static int
PyHCIDevice_init(PyHCIDevice *self, PyObject *args, PyObject *kwds)
{
	char *name, *add;
	char *kwlist[] =  {
			"name",
			"add",
			NULL
	};

	if (PyBtDeviceType.tp_init((PyObject *) self, args, kwds) < 0){
		return -1;
	}

	if(! PyArg_ParseTupleAndKeywords(args, kwds, "|ss", kwlist, &name, &add) )  {
		return -1;
	}

	self->devid  = 0;
	return 0;
}


static void
PyHCIDevice_dealloc(PyHCIDevice *self)
{
	PyBtDeviceType.tp_dealloc((PyObject *)self);
}

static PyMemberDef PyHCIDevice_members[] =  {
		{"hcidevid", T_USHORT, offsetof(PyHCIDevice, devid), 0,
				"Device ID"},
		{ NULL }
};

static PyTypeObject PyHCIDeviceType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btsniff.HCIDevice",             /*tp_name*/
		sizeof(PyHCIDevice),             /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor)PyHCIDevice_dealloc, /*tp_dealloc*/
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
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE , /*tp_flags*/
		"Abstraction for a Bluetooth device",      /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,             /* tp_methods */
		PyHCIDevice_members,             /* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	   (initproc)PyHCIDevice_init,      /* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};


/* Initialize the method map */
static PyMethodDef BaseSniffMethods[] =
{
		{"get_timer", (PyCFunction)basesniff_get_timer, METH_VARARGS, "gets the clock" },
		{"set_filter", (PyCFunction)basesniff_set_filter, METH_VARARGS, "sets filters. called with -f option" },
		{"stop_sniff", (PyCFunction)basesniff_sniff_stop, METH_VARARGS, "stops sniffing"},
		{"start_sniff", (PyCFunction)basesniff_sniff_start, METH_VARARGS, "starts the sniffing" },
		{"start_capture", (PyCFunction)basesniff_sniff, METH_VARARGS | METH_KEYWORDS, "when sniffing is started, this prints data and dumps to file" },
		{"close_device", (PyCFunction)basesniff_close_hcidev, METH_VARARGS, "Close a HCI device"},
		{"open_device", (PyCFunction)basesniff_open_hcidev, METH_VARARGS, "Open a HCI device"},
		{"get_device_list", (PyCFunction) basesniff_getdevlist, METH_NOARGS, "Get a list of connected HCI devices"},
		{NULL, NULL, 0, NULL}
};

/* Initialize the module */
PyMODINIT_FUNC
initbtsniff(void)
{
	PyObject *m;

	// These constant objects are used to initialize layer objects in
	// the above function
	EMPTY_TUPLE = PyTuple_New(0);
	EMPTY_DICT  = PyDict_New();

	PySniffHandlerType.tp_new = PyType_GenericNew;
	PyBtDeviceType.tp_new = PyType_GenericNew;

	PyHCIDeviceType.tp_base = &PyBtDeviceType;
	PyHCIDeviceType.tp_new = PyType_GenericNew;

	SniffError = PyErr_NewException("btsniff.SniffError", NULL, NULL);

	if(PyType_Ready(&PyStateType) < 0
		|| PyType_Ready(&PySniffHandlerType) < 0
		|| PyType_Ready(&PyBtDeviceType) < 0
		|| PyType_Ready(&PyHCIDeviceType) < 0 )
		return;

	//Initialize layer types. Will be used in the above functions.
	//Take note, initialized but their reference counts are not incremented
	setup_layer_types();

	m = Py_InitModule3("btsniff", BaseSniffMethods, "Main sniffing module");

	if( m == NULL)
		return;

	Py_INCREF(&PyStateType);
	Py_INCREF(&PySniffHandlerType);
	Py_INCREF(SniffError);

	PyModule_AddObject(m, "BtDevice", (PyObject *)&PyBtDeviceType);
	PyModule_AddObject(m, "HCIDevice", (PyObject *)&PyHCIDeviceType);
	PyModule_AddObject(m, "CaptureState", (PyObject *)&PyStateType);
	PyModule_AddObject(m, "SniffHandler", (PyObject *) &PySniffHandlerType);
	PyModule_AddObject(m, "SniffError", SniffError);

	PyModule_AddIntMacro(m, HCI_EVENT_PKT);
	PyModule_AddIntMacro(m, HCI_ACLDATA_PKT);
	PyModule_AddIntMacro(m, HCI_COMMAND_PKT);
	PyModule_AddIntMacro(m, HCI_SCODATA_PKT);
	PyModule_AddIntMacro(m, HCI_VENDOR_PKT);

}
