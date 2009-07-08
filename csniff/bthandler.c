/*
 * bthandler.c
 *
 *  Created on: Jul 5, 2009
 *      Author: quekshuy
 */


/* TODO
 *
 * 1. Define an event handler object (interface) that can be called whenever we receive a BT packet
 * 2. Define data structure for LMP packets
 *
 */

#include "bthandler.h"
#include "structmember.h"

/* Object definition for PyLMPPacket */
static int
PyLMPPacket_init(PyLMPPacket *self, PyObject *args, PyObject *kwds)
{
	self->tid = -1;
	self->op1 = -1;
	self->op2 = -1;
	self->payload_list = PyList_New(0);
	if(! self->payload_list)
		return -1;
	return 0;
}

static void
PyLMPPacket_dealloc(PyLMPPacket *self)
{
	Py_XDECREF(self->payload_list);
	self->ob_type->tp_free((PyObject *) self );
}

static PyObject *
PyLMPPacket_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyLMPPacket *self;
	self = (PyLMPPacket *) type->tp_alloc(type, 0);
	self->op1 = -1;
	self->op2 = -1;
	self->tid = -1;
	self->payload_list = NULL;

	return (PyObject *) self;
}

static PyMemberDef PyLMPPacket_members[] =  {
		{"tid", T_UBYTE, offsetof(PyLMPPacket, tid), 0, "Transaction ID"},
		{"op1", T_UBYTE, offsetof(PyLMPPacket, op1), 0, "Op code 1"},
		{"op2", T_UBYTE, offsetof(PyLMPPacket, op2), 0, "Op code 2"},
		{"data", T_OBJECT_EX, offsetof(PyLMPPacket, payload_list), 0, "Python list of integers corresponding to the payload"},
		{ NULL }
};

PyTypeObject PyLMPPacketType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"sniff._LMPPacket",             /*tp_name*/
		sizeof(PyLMPPacket),             /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor) PyLMPPacket_dealloc, /*tp_dealloc*/
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
		"LMP PDU encapsulated.",      /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,             /* tp_methods */
		PyLMPPacket_members,             /* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	   (initproc)PyLMPPacket_init,      /* tp_init */
		0,                         /* tp_alloc */
		PyLMPPacket_new,                 /* tp_new */
};


/*
 * Definition for SniffHandler
 */


static PyObject *
PySniffHandler_pktreceived(PyObject *dummy, PyObject *args, PyObject *kwds)
{
	PyObject *pkt = NULL;
	//Do basic error checking of arguments
	char *kwlist[] =  { "packet", NULL };
	if (! PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &pkt))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef PySniffHandler_methods[] =  {
		{"recvpacket", (PyCFunction)PySniffHandler_pktreceived, METH_VARARGS | METH_KEYWORDS,
				"Callback method for packet is received"},
		{NULL, NULL, 0, NULL}
};

PyTypeObject PySniffHandlerType =  {

		PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"sniff.SniffHandler",             /*tp_name*/
		sizeof(PySniffHandler),             /*tp_basicsize*/
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
		"Handles the events when packets are received",      /* tp_doc */
		0,                          /* tp_traverse */
		0,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		PySniffHandler_methods,             /* tp_methods */
		0,             			/* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
		0,      					/* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};


