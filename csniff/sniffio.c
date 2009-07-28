
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>
#include <fcntl.h>
#include <err.h>

#include "basesniffmodule.h"
#include "bthandler.h"
#include "sniffio.h"
#include "structmember.h"

PyObject *SniffSniffError;

/*
 * Parameters:
 * 	isMaster	- indicates whether host is the master in the communications
 * 	pkt			- LMPPacket
 */
static PyObject *
_dump_events(int dumpfd, uint8_t isMaster, PyObject *pkt)
{
	struct hcidump_hdr dh;
	PyLMPPacket *lmppkt = (PyLMPPacket *) ((PySniffPacket *)pkt)->_payloadpkt;
	hci_event_hdr evt;
	uint8_t type = HCI_EVENT_PKT;
	unsigned char csr_lmp[1 + 1 + 17 + 1];
	int totlen = sizeof(type) + sizeof(evt) + sizeof(csr_lmp);
	unsigned char *p = csr_lmp;
	int len, i, payload_byte, wresult;

	if(dumpfd == -1){
		RETURN_VOID
	}

	/* hcidump header */
	memset(&dh, 0, sizeof(dh));
	dh.len	= totlen;
	dh.in	= 1;
	dh.ts_sec = 0;
	dh.ts_usec = 0;

	Py_BEGIN_ALLOW_THREADS
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

	/* event header */
	memset(&evt, 0, sizeof(evt));
	evt.evt		= EVT_VENDOR;
	evt.plen	= sizeof(csr_lmp);

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, &evt, sizeof(evt));
	Py_END_ALLOW_THREADS

	if( wresult != sizeof(evt))
	{
		PyErr_SetString(SniffSniffError, "_dump_events: error writing event header");
		return NULL;
	}

	/* CSRized LMP packet */
	memset(csr_lmp, 0, sizeof(csr_lmp));
	*p++ = 20; //Channel ID
	*p++ = isMaster ? 0x10 : 0x0f;
	*p++ = (lmppkt->op1 << LMP_OP1_SHIFT) | lmppkt->tid;
	if(lmppkt->op1 >= 124 && lmppkt->op1 <= 127)
		*p++ = lmppkt->op2;

	len = PyList_Size(lmppkt->payload_list);
	assert(len <= sizeof(csr_lmp) - 2);
	for(i = 0; i < len; i++)
	{
		payload_byte = (int) PyInt_AsLong(PyList_GetItem(lmppkt->payload_list, i));
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
	hci_acl_hdr acl;
	PyGenericPacket *l2cappkt = (PyGenericPacket *)((PySniffPacket *)pkt)->_payloadpkt;
	int len = PyList_Size((PyObject *)l2cappkt->data), i, wresult;
	int totlen = sizeof(type) + sizeof(acl) + len;
	uint8_t buf[len];

	if (dumpfd == -1)
		RETURN_VOID

	memset(&dh, 0, sizeof(dh));
	dh.len		= totlen;
	dh.in		= 1;
	dh.ts_sec	= 0;
	dh.ts_usec	= 0;

	Py_BEGIN_ALLOW_THREADS
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

	memset(&acl, 0, sizeof(acl));
	acl.dlen	= len;
	acl.handle	= acl_handle_pack(0, llid);

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, &acl, sizeof(acl));
	Py_END_ALLOW_THREADS

	if (wresult != sizeof(acl))
	{
		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing acl header");
		return NULL;
	}

	for(i = 0; i < len; i++)
		buf[i] = (uint8_t) PyInt_AsLong(PyList_GetItem((PyObject *)l2cappkt->data, i));

	Py_BEGIN_ALLOW_THREADS
	wresult = write(dumpfd, buf, len);
	Py_END_ALLOW_THREADS

	if(wresult != len)
	{
		PyErr_SetString(SniffSniffError, "_dump_l2cap: error writing data");
		return NULL;
	}
	RETURN_VOID
}

/*
 * Parameters:
 * 	dumpfd 		- file descriptor for dump file
 * 	pkt 		- packet
 * 	type		- HCI packet type
 *  isMaster	- indicates if the controller belongs to the master
 */
static PyObject *
hciwrite(int dumpfd, PyObject *pkt, uint8_t type, int llid, uint8_t isMaster)
{
	switch(type){
		case HCI_ACLDATA_PKT:
			return _dump_l2cap(dumpfd, llid, pkt);
			break;
		case HCI_EVENT_PKT:
			return _dump_events(dumpfd, isMaster, pkt);
			break;
		default:
			err(1, "hciwrite: None chosen");
			break;
	}
	RETURN_VOID
}

static PyObject *
sniffio_writetofile(PyObject *self, PyObject *args, PyObject *kwds)
{
	char *fname;
	PyObject *packet = NULL, *dmp_result = NULL;
	unsigned char type, isMaster;
	int fd, llid;

	char *kwlist[] = {
			"hcipkttype",
			"llid",
			"ismaster",
			"packet",
			"filename",
			NULL
	};

	if(!PyArg_ParseTupleAndKeywords(args, kwds, "bibOs:writetofile", kwlist,
			&type, &llid, &isMaster, &packet, &fname))
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
		 dmp_result = hciwrite(fd, packet, (uint8_t)type, llid, (uint8_t) isMaster);
		 Py_BEGIN_ALLOW_THREADS
		 close(fd);
		 Py_END_ALLOW_THREADS

	 }

	 return dmp_result;
}

//Untested
static PyObject *
sniffio_write(PyObject *self, PyObject *args, PyObject *kwds)
{
	PyState *state;
	PyObject *packet;
	uint8_t type, isMaster;
	int llid;

	char *kwlist[] = {
		"hcipkttype",
		"llid",
		"ismaster",
		"packet",
		"sniffstate",
		NULL
	};

	if(!PyArg_ParseTupleAndKeywords(args, kwds, "bibOO", kwlist,
			&type, &llid, &isMaster, &packet, &state))
		return NULL;

	return hciwrite(state->s_dump, packet, type, llid, isMaster);
}


static PyMethodDef PyHCIWriter_methods[] =
{
		{"writetofile", (PyCFunction)sniffio_writetofile, METH_VARARGS | METH_KEYWORDS, "Writes to HCIDump format. Must specify filename." },
		{"write", (PyCFunction)sniffio_write, METH_VARARGS | METH_KEYWORDS, "Writes to HCIDump format" },
		{NULL}
};

static PyTypeObject PyHCIWriterType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"sniff_fileio.HCIDumpWriter",        /*tp_name*/
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
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
		"PyState object will ultimately be converted into a SniffSession. This is struct state from the original code",           /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		PyHCIWriter_methods,		/* tp_methods */
		0,					      /* tp_members */
		0,     /* tp_getset */
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
initsniff_fileio(void)
{
	PyObject *m, *import_m, *importdict;

	PyHCIWriterType.tp_new = PyType_GenericNew;
	if(PyType_Ready(&PyHCIWriterType) < 0)
		return;

	m = Py_InitModule3("sniff_fileio", NULL, "Sniffing file IO module");
	import_m = PyImport_ImportModule("umit.bluetooth.sniff");

	if(m == NULL || import_m == NULL)
		return;
	//Importing SniffError so it can be used in this module
	importdict = PyModule_GetDict(import_m);
	SniffSniffError = PyDict_GetItemString(importdict, "SniffError");

	Py_INCREF(&PyHCIWriterType);
	PyModule_AddObject(m, "HCIWriter", (PyObject *) &PyHCIWriterType);

}
