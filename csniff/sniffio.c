
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>
#include <fcntl.h>
#include <err.h>

#include "basesniffmodule.h"
#include "layers.h"
#include "sniffio.h"
#include "structmember.h"

PyObject *SniffSniffError;
PyObject *EMPTY_TUPLE, *EMPTY_DICT;

/*
 *
 * There is a problem with our file IO beginning with this method. Firstly, we lose any knowledge of the
 * length of the original LMP packet. As a result, reading from the HCIDUMP file may yield inaccurate
 * captures. This is not the case with ACL data.
 *
 * @param dumpfd File descriptor of dump file.
 * @param is_master Indicates if the packet is sniffed from the master node in the piconet/pair
 * @param pkt PySniffRaw sniffed packet.
 *
 * @return NULL if error.
 *
 */
static PyObject *
_dump_events(int dumpfd, uint8_t is_master, PyObject *pkt)
{
	struct hcidump_hdr dh;
	hci_event_hdr evt;
	uint8_t type = HCI_EVENT_PKT, tmpOp, tmpTid;
	unsigned char csr_lmp[1 + 1 + 17 + 1], *p = csr_lmp;
	int totlen = sizeof(type) + sizeof(evt) + sizeof(csr_lmp);
	int len, i, payload_byte, wresult;

	PyLayerUnit *lmppkt = (PyLayerUnit *) ((PySniffRaw *)pkt)->raw.payload;
	PyLMPHdr *hdr = (PyLMPHdr *)lmppkt->hdr;

	if(dumpfd == -1){
		RETURN_VOID
	}

	Py_BEGIN_ALLOW_THREADS
	/* hcidump header */
	memset(&dh, 0, sizeof(dh));
	dh.len	= totlen;
	dh.in	= 1;
	dh.ts_sec = 0;
	dh.ts_usec = 0;
	wresult = write(dumpfd, &dh, sizeof(dh));
	Py_END_ALLOW_THREADS

	if(wresult != sizeof(dh))	 {
		PyErr_SetString(SniffSniffError, "_dump_events: error writing hcidump header");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, &type, sizeof(type));
	Py_END_ALLOW_THREADS

	if(wresult != sizeof(type))
	{
		PyErr_SetString(SniffSniffError, "_dump_events: error writing type");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	/* event header */
	memset(&evt, 0, sizeof(evt));
	evt.evt		= EVT_VENDOR;
	evt.plen	= sizeof(csr_lmp);

	wresult = write(dumpfd, &evt, sizeof(evt));
	Py_END_ALLOW_THREADS

	if( wresult != sizeof(evt))
	{
		PyErr_SetString(SniffSniffError, "_dump_events: error writing event header");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	/* CSRized LMP packet */
	memset(csr_lmp, 0, sizeof(csr_lmp));
	*p++ = 20; //Channel ID
	*p++ = is_master ? 0x10 : 0x0f;
	Py_END_ALLOW_THREADS

	tmpOp = hdr->op1;
	tmpTid = hdr->tid;
	*p++ = (tmpOp << LMP_OP1_SHIFT) | tmpTid;
	if(tmpOp >= 124 && tmpOp <= 127)
		*p++ = hdr->op2;

	//Type checking for payload
	if(PySequence_Check(lmppkt->payload->rawdata) == 0 )
	{
		// TODO: do error setting
		return NULL;
	}

	len = PySequence_Size(lmppkt->payload->rawdata);
	assert(len <= sizeof(csr_lmp) - 2);
	for(i = 0; i < len; i++)
	{
		payload_byte = (int) PyInt_AsLong(PySequence_GetItem(lmppkt->payload->rawdata, i));
		if(payload_byte < 0 && PyErr_Occurred())
		{
			return NULL;
		}
		else
			*p++ = (uint8_t) payload_byte;
	}

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, csr_lmp, sizeof(csr_lmp));
	Py_END_ALLOW_THREADS

	if(wresult != sizeof(csr_lmp))
	{
		PyErr_SetString(SniffSniffError, "_dump_events: error writing pdu");
		return NULL;
	}

	RETURN_VOID
}

static PyObject *
_dump_l2cap(int dumpfd, int llid, PyObject *pkt)
{
	struct hcidump_hdr dh;
	uint8_t type = HCI_ACLDATA_PKT;
	int len, i, wresult, totlen;
	uint8_t *buf;
	hci_acl_hdr acl;
	PyLayerUnit *l2cappkt = (PyLayerUnit *)((PySniffRaw *)pkt)->raw.payload;
	PyObject *l2capdata = PyObject_GetAttrString((PyObject *)l2cappkt, "rawdata");

	Py_BEGIN_ALLOW_THREADS
	//Type checking. Check that is sequence
	if(PySequence_Check(l2capdata) == 0)
		return NULL;

	len = PySequence_Size(l2capdata);
	buf = malloc(len * sizeof(uint8_t));
	totlen = sizeof(type) + sizeof(acl) + len;

	Py_END_ALLOW_THREADS
	if (dumpfd == -1){
		RETURN_VOID
	}

	Py_BEGIN_ALLOW_THREADS
	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	wresult = write(dumpfd, &dh, sizeof(dh));
	Py_END_ALLOW_THREADS

	if ( wresult != sizeof(dh))
	{

		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing hcidump header");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, &type, sizeof(type));
	Py_END_ALLOW_THREADS

	if (wresult != sizeof(type))
	{
		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing type");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	memset(&acl, 0, sizeof(acl));
	acl.dlen	= len;
	acl.handle	= acl_handle_pack(0, llid);

	wresult = write(dumpfd, &acl, sizeof(acl));
	Py_END_ALLOW_THREADS

	if (wresult != sizeof(acl))
	{
		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing acl header");
		return NULL;
	}

	for(i = 0; i < len; i++)
		buf[i] = (uint8_t) PyInt_AsLong(PySequence_GetItem(l2capdata, i));

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, buf, len);
	free(buf);
	Py_END_ALLOW_THREADS

	if(wresult != len)
	{
		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing data");
		return NULL;
	}

	RETURN_VOID
}

/*
 *
 * @param dumpfd File descriptor for the dump file.
 * @param pkt PySniffRaw packet
 * @param type HCI Packet Type.
 * @param is_master Indicates if the packet originated from the master.
 */
static PyObject *
hciwrite(int dumpfd, PyObject *pkt, uint8_t type, int llid, uint8_t is_master)
{
	switch(type){
		case HCI_ACLDATA_PKT:
			return _dump_l2cap(dumpfd, llid, pkt);
			break;
		case HCI_EVENT_PKT:
			return _dump_events(dumpfd, is_master, pkt);
			break;
		default:
			err(1, "hciwrite: None chosen");
			break;
	}
	RETURN_VOID
}

static PyObject *
get_llid(PyObject *packet)  {
	return PyObject_GetAttrString(packet, "llid");
}

static PyObject *
get_type(PyObject *packet)  {

	PyObject * llid = get_llid(packet);

	if (llid == NULL)
		return NULL;

	else if (LLID_LMP == PyInt_AsLong(llid))
		return PyInt_FromLong((long)HCI_EVENT_PKT);

	return PyInt_FromLong((long) HCI_ACLDATA_PKT);
}

static PyObject *
is_master_packet(PyObject *packet)  {
	return PyObject_GetAttrString(packet, "is_src_master");
}

/**
 * @param filepath 	File path.
 * @param packets 	List of SniffRaw packets.
 */
static PyObject *
sniffio_writetofile(PyObject *self, PyObject *args, PyObject *kwds)
{
	char *fname;
	PyObject *packets = NULL, *packet = NULL, *dmp_result = NULL;
	PyObject *llid, *type, *is_src_master;
	int fd, plist_len, i;

	char *kwlist[] = {
			"filepath",
			"packets",
			NULL
	};

	if(!PyArg_ParseTupleAndKeywords(args, kwds, "sbibO:writetofile", kwlist,
			 &fname, &packets))
	{
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	fd = open(fname, O_APPEND | O_WRONLY | O_CREAT, 0644);
	Py_END_ALLOW_THREADS

	 if(fd < 0)
	 {
		 PyErr_SetString(SniffSniffError, "writetofile: error opening file");
		 return NULL;
	 }
	 else{

		 if (PyList_Check(packets)) {
			 PyErr_SetString(SniffSniffError, "writetofile: needs a list of packets");
			 return NULL;
		 }
		 else {

			 plist_len = PyList_Size(packets);
			 for (i = 0 ; i <  plist_len; i++)  {

				 packet = PyList_GetItem(packets, i);

				 Py_BEGIN_ALLOW_THREADS
				 llid = get_llid(packet);
				 type = get_type(packet);
				 is_src_master = is_master_packet(packet);
				 Py_END_ALLOW_THREADS

				 if (llid == NULL || type == NULL || is_src_master == NULL)
					 return NULL;

				 dmp_result = hciwrite(fd, packet, (uint8_t) PyInt_AsLong(type), (int) PyInt_AsLong(llid),
						 (uint8_t) PyInt_AsLong(is_src_master));

				 if(!dmp_result) return dmp_result;
			 }
		 }

		 Py_BEGIN_ALLOW_THREADS
		 close(fd);
		 Py_END_ALLOW_THREADS
	 }

	 return dmp_result;
}


static PySniffRaw *
create_sniff_object(void)  {

	PySniffRaw *sniff;
	PySniffHdr *shdr;

	sniff = (PySniffRaw *) PySniffRawType.tp_new(&PySniffRawType, NULL, NULL);
	if (PySniffRawType.tp_init((PyObject *) sniff, EMPTY_TUPLE, EMPTY_DICT) < 0)  {
		return NULL;
	}

	shdr = (PySniffHdr *)PySniffHdrType.tp_new(&PySniffHdrType, NULL, NULL);
	if (PySniffHdrType.tp_init((PyObject *) shdr, EMPTY_TUPLE, EMPTY_DICT) < 0) {
		return NULL;
	}

	sniff->raw.hdr = (PyLayerHeader *) shdr;
	return sniff;
}


static PyRawObject *
create_raw_object(uint8_t *bytes, int len) {

	PyObject *list;
	PyRawObject *raw;

	list = PyList_New(0);

	raw = (PyRawObject *) PyRawObjectType.tp_new(&PyRawObjectType, NULL, NULL);
	if (PyRawObjectType.tp_init((PyObject *) raw, EMPTY_TUPLE, EMPTY_DICT )< 0)  {
		return NULL;
	}

	while(len--)  {
		PyList_Append(list, PyInt_FromLong((long) *bytes++));
	}

	raw->rawdata = list;
	return raw;
}

static PyObject *
extract_l2cap(int fd)
{
	PyObject *data_list;
	PyRawObject *payload;
	PySniffRaw *sniff;
	hci_acl_hdr acl;
	uint8_t *p;

	data_list = PyList_New(0);
	if(0 > read(fd, &acl, sizeof(acl))) {
		return NULL;
	}
	else {

		p =(uint8_t *) malloc(acl.dlen);
		if (read(fd, p, acl.dlen) > -1)
			payload = create_raw_object(p, acl.dlen);
		else
			return NULL;
	}

	sniff = create_sniff_object();
	((PySniffHdr *)sniff->raw.hdr)->dlen = PyList_Size(data_list);

	payload->rawdata = data_list;
	sniff->raw.payload = payload;

	return (PyObject *) sniff;
}

static PyObject *
extract_lmp(int fd) {

	PySniffRaw *sniff;
	PyLMPHdr *lmphdr;
	PyRawObject *lmp_payload;
	PyLayerUnit *lmp;

	hci_event_hdr evt;
	uint8_t len;
	unsigned char csr_lmp[1 + 1 + 17], *p = csr_lmp + 1 + 1;


	if (read(fd, &evt, sizeof(evt)) < 0 ||
		read(fd, csr_lmp, sizeof(csr_lmp)) < 0)

		return NULL;

	lmphdr = (PyLMPHdr *) PyLMPHdrType.tp_new(&PyLMPHdrType, NULL, NULL);
	if (PyLMPHdrType.tp_init((PyObject *)lmphdr, EMPTY_TUPLE, EMPTY_DICT) < 0)
		return NULL;

	len  = 17; //we assume that the maximum size of a LMP packet is 17 bytes. Correct at time of writing.
	memset(csr_lmp, 0, sizeof(csr_lmp));

	lmphdr->tid = *p & LMP_TID_MASK;
	lmphdr->op1 = *p++ >> LMP_OP1_SHIFT;
	len--;
	if (lmphdr->op1 >= 124 && lmphdr->op1 <= 127) {
		lmphdr->op2 = *p++;
		len--;
	}

	lmp_payload = create_raw_object(p, len);

	lmp = (PyLayerUnit *) PyLayerUnitType.tp_new(&PyLayerUnitType, NULL, NULL);
	if (PyLayerUnitType.tp_init((PyObject *) lmp, EMPTY_TUPLE, EMPTY_DICT) < 0) {
		return NULL;
	}

	lmp->hdr = (PyLayerHeader *) lmphdr;
	lmp->payload = lmp_payload;

	sniff = create_sniff_object();
	sniff->raw.payload = (PyRawObject *) lmp;
	return (PyObject *) sniff;
}


static PyObject *
extract_packet(int fd)  {

	struct hcidump_hdr hhd;
	uint8_t type;
	PyObject *packet;

	Py_BEGIN_ALLOW_THREADS
	if (0 > read(fd, &hhd, sizeof(hhd)) ||
		0 > read(fd, &type, sizeof(type)))  {
		return NULL;
	}
	else {
		// Do analysis of hcidump/type info
		if (type == HCI_ACLDATA_PKT) {
			packet = extract_l2cap(fd);
		}
		else {
			packet = extract_lmp(fd);
		}
	}
	Py_END_ALLOW_THREADS
	return packet;
}

/**
 * Open file and read packets
 * @param filepath Path to hcidump file
 * @return A list of PySniffRaw packets
 */
static PyObject *
sniffio_readfile(PyObject *self, PyObject *arg) {

	PyObject *plist, *tmp;
	char *path;
	int fd;

	plist = PyList_New(0);

	if (!PyArg_ParseTuple(arg, "s", &path))
	{
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	fd = open(path, O_RDONLY, 0666);
	if (fd >= 0)  {
		if ((tmp = extract_packet(fd)) != NULL)  {
			PyList_Append(plist, tmp);
		}
		else {
			close(fd);
		}
	}
	Py_END_ALLOW_THREADS
	return plist;

}

static PyMethodDef PyHCIWriter_methods[] =
{
		{"write_filename", (PyCFunction)sniffio_writetofile, METH_VARARGS | METH_KEYWORDS, "Writes to HCIDump format. Must specify filename." },
		{"read_filename",  (PyCFunction)sniffio_readfile, METH_VARARGS, "Reads from a HCIDUMP file and returns a list of sniffed packets. Experimental." },
		{NULL}
};

static PyTypeObject PyHCIWriterType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btsniff_fileio.HCIDumpWriter",        /*tp_name*/
		sizeof(PyHCIWriter),      /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		0, /*tp_dealloc*/
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
		Py_TPFLAGS_DEFAULT |
		Py_TPFLAGS_BASETYPE, 	   /*tp_flags*/
		"HCIDumpWriter writes",           /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		PyHCIWriter_methods,		/* tp_methods */
		0,					      	/* tp_members */
		0,    						/* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	    0,				      		/* tp_init */
		0,                         /* tp_alloc */
		0,                 	/* tp_new use GenericNew*/
};


PyMODINIT_FUNC
initbtsniff_fileio(void)
{
	PyObject *m, *import_m, *importdict;

	//Initialize dummy variables for use in initializing packets
	EMPTY_TUPLE = PyTuple_New(0);
	EMPTY_DICT = PyDict_New();

	PyHCIWriterType.tp_new = PyType_GenericNew;
	if(PyType_Ready(&PyHCIWriterType) < 0)
		return;

	m = Py_InitModule3("btsniff_fileio", NULL, "Sniffing file IO module");
	import_m = PyImport_ImportModule("umit.bluetooth.btsniff");

	if(m == NULL || import_m == NULL)
		return;
	//Importing SniffError so it can be used in this module
	importdict = PyModule_GetDict(import_m);
	SniffSniffError = PyDict_GetItemString(importdict, "SniffError");

	Py_INCREF(&PyHCIWriterType);
	PyModule_AddObject(m, "HCIWriter", (PyObject *) &PyHCIWriterType);

}
