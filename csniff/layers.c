
#include "layers.h"
#include <string.h>
#include "structmember.h"


/**
 * Methods to be overwritten for implementations of PyRawObject
 */
static PyObject *
PyRawObject_repr(PyRawObject *obj)
{
	PyObject *data_repr;
	const char *name = obj->ob_type->tp_name, *sep = ": ";
	int namelen = strlen(name);
	char hdr[namelen + 3];
	memcpy(hdr, name, namelen);
	memcpy(hdr + namelen, sep, 3); //3 because ": \0"
	data_repr = PyString_FromString(hdr);
	PyString_Concat(&data_repr,  obj->data->ob_type->tp_repr(obj->data));
	return data_repr;
}

static int
PyRawObject_traverse(PyRawObject *self, visitproc visit, void *arg)
{
	Py_VISIT(self->data);
	return 0;
}

static int
PyRawObject_clear(PyRawObject *self)
{
	PyObject *tmp;
	tmp = self->data;
	self->data = NULL;
	Py_XDECREF(tmp);
	return 0;
}

static int
PyRawObject_init(PyRawObject *self, PyObject *args, PyObject *kwds)
{
	return 0;
}

static PyObject *
PyRawObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyRawObject *self;
	self  = (PyRawObject *)type->tp_alloc(type, 0);
	if(self != NULL)
		self->data = Py_None;
	Py_INCREF(self->data);

	return (PyObject *)self;
}

static void
PyRawObject_dealloc(PyRawObject *self)
{
	PyRawObject_clear(self);
	self->ob_type->tp_free((PyObject *) self );
}

/**
 * PyRawObject has only one single attribute: data (which should be of type sequence)
 * This returns raw data.
 */
static PyMemberDef PyRawObject_members[] = {
		{"rawdata", T_OBJECT, offsetof(PyRawObject, data), 0, PyDoc_STR("Data attribute.")},
		{NULL}
};

PyTypeObject PyRawObjectType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btlayers.BtRaw",             /*tp_name*/
		sizeof(PyRawObject),             /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor) PyRawObject_dealloc, /*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		(reprfunc) PyRawObject_repr, /*tp_repr*/
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
		"Raw Bluetooth layer packet.",      /* tp_doc */
		(traverseproc)PyRawObject_traverse,                          /* tp_traverse */
		(inquiry)PyRawObject_clear,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,    			         /* tp_methods */
		PyRawObject_members,             /* tp_members */
		0,                         /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	   (initproc)PyRawObject_init,      /* tp_init */
		0,                         /* tp_alloc */
		PyRawObject_new,                 /* tp_new */
};

/***
 * Definitions for PyLayerHeader.
 * Inherits everything from PyRawObject
 */

static int
PyLayerHeader_init(PyLayerHeader *self, PyObject *args, PyObject *kwds)
{
	if(PyRawObjectType.tp_init((PyObject *)self, args, kwds) < 0)
		return -1;
	return 0;
}

static int
PyLayerHeader_traverse(PyLayerHeader *self, visitproc visit, void *arg)
{
	return PyRawObjectType.tp_traverse((PyObject *)self, visit, arg);
}

static int
PyLayerHeader_clear(PyLayerHeader *self)
{
	return PyRawObjectType.tp_clear((PyObject *) self);
}

static void
PyLayerHeader_dealloc(PyLayerHeader *self)
{
	PyRawObjectType.tp_dealloc((PyObject *) self);
}

static PyObject *
PyLayerHeader_getdata(PyLayerHeader *self, void *closure)
{
	return PyTuple_New(0);
}

static PyGetSetDef PyLayerHeader_getseters[] =  {
		{"rawdata", (getter) PyLayerHeader_getdata,
				NULL, "Get raw data for header in tuple representation."
		},
		{NULL}
};

PyTypeObject PyLayerHeaderType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         				/*ob_size*/
		"btlayers.BtLayerHeader",       		/*tp_name*/
		sizeof(PyLayerHeader),      			/*tp_basicsize*/
		0,                         				/*tp_itemsize*/
		(destructor) PyLayerHeader_dealloc,		/*tp_dealloc*/
		0,                         				/*tp_print*/
		0,                         				/*tp_getattr*/
		0,                         				/*tp_setattr*/
		0,                         				/*tp_compare*/
		0, 										/*tp_repr*/
		0,                         				/*tp_as_number*/
		0,                         				/*tp_as_sequence*/
		0,                         				/*tp_as_mapping*/
		0,                         				/*tp_hash */
		0,                         				/*tp_call*/
		0,                         				/*tp_str*/
		0,                         				/*tp_getattro*/
		0,                         				/*tp_setattro*/
		0,                         				/*tp_as_buffer*/
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE
		| Py_TPFLAGS_HAVE_GC,					 /*tp_flags*/
		"Bluetooth layer header.",      		/* tp_doc */
		(traverseproc) PyLayerHeader_traverse,  /* tp_traverse */
		(inquiry)PyLayerHeader_clear,			/* tp_clear */
		0,                          			/* tp_richcompare */
		0,                          			/* tp_weaklistoffset */
		0,                          			/* tp_iter */
		0,                          			/* tp_iternext */
		0,    			         				/* tp_methods */
		0,        								/* tp_members */
		PyLayerHeader_getseters, 				/* tp_getset */
		0,                         				/* tp_base */
		0,                         				/* tp_dict */
		0,                         				/* tp_descr_get */
		0,                         				/* tp_descr_set */
		0,                         				/* tp_dictoffset */
	    (initproc)PyLayerHeader_init,      		/* tp_init */
		0,                        			 	/* tp_alloc */
		0,                 						/* tp_new */
};


/**
 * PyLayerUnit Definitions
 * A PyLayerUnit is composed of its header and its payload, which
 * can be another PyRawObject
 */


/**
 * We do not allow an instance of a PyLayerUnit to be created without
 * its header. Such an instance would be meaningless.
 */
static int
PyLayerUnit_init(PyLayerUnit *self, PyObject *args, PyObject *kwds)
{
	char *kwlist[] =  {
			"header",
			"payload",
			NULL
	};

	self->hdr = NULL;
	self->payload = NULL;

	if(PyRawObjectType.tp_init((PyObject *)self, args, kwds) < 0)
		return -1;

	if(!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist,
			&self->hdr, &self->payload))
		return -1;

	if(self->payload == NULL)
	{
		self->payload = (PyRawObject *) Py_None;
		Py_INCREF(self->payload);
	}

	return 0;
}

static int
PyLayerUnit_traverse(PyLayerUnit *self, visitproc visit, void *arg)
{
	Py_VISIT(self->hdr);
	Py_VISIT(self->payload);
	return PyRawObjectType.tp_traverse((PyObject *)self, visit, arg);
}

static int
PyLayerUnit_clear(PyLayerUnit *self)
{
	PyObject *tmp;
	tmp = (PyObject *)self->hdr;
	self->hdr = NULL;
	Py_XDECREF(tmp);

	tmp = (PyObject *)self->payload;
	self->payload = NULL;
	Py_XDECREF(tmp);

	return PyRawObjectType.tp_clear((PyObject *) self);
}

static void
PyLayerUnit_dealloc(PyLayerUnit *self)
{
	PyLayerUnit_clear(self);
	PyRawObjectType.tp_dealloc((PyObject *) self);
}

static PyObject *
PyLayerUnit_getdata(PyLayerUnit *self, void *closure)
{
	PyObject *hdrraw, *payloadraw, *ret = NULL;

	if((hdrraw = PyObject_GetAttrString((PyObject *)self->hdr, "rawdata")) != NULL
			&& PyTuple_Check(hdrraw))
	{
		if(self->payload != (PyRawObject *)Py_None &&
			(payloadraw = PyObject_GetAttrString((PyObject *)self->payload, "rawdata")) != NULL
			&& PyTuple_Check(payloadraw))
		{
			ret = PySequence_Concat(payloadraw, hdrraw);
		}
		else if(self->payload == (PyRawObject *) Py_None)
		{
			ret = hdrraw;
		}
	}
	return ret;
}

static PyGetSetDef PyLayerUnit_getseters[] =  {
		{"rawdata", (getter) PyLayerUnit_getdata,
				NULL,
				"Data in tuple representation.",
				NULL
		},
		{NULL}
};

PyTypeObject PyLayerUnitType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btlayers.BtLayerUnit",         /*tp_name*/
		sizeof(PyLayerUnit),      /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor) PyLayerUnit_dealloc,		/*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		0, 							/*tp_repr*/
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
		"A packet from a Bluetooth layer.",      /* tp_doc */
		(traverseproc) PyLayerUnit_traverse,    /* tp_traverse */
		(inquiry)PyLayerUnit_clear,                          /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,    			         /* tp_methods */
		0,        				/* tp_members */
		PyLayerUnit_getseters,  /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	    (initproc)PyLayerUnit_init,      	/* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};

/**
 * LMP header
 */

static int
PyLMPHdr_init(PyLMPHdr *self, PyObject *args, PyObject *kwds)
{
	uint8_t tid = 0, op1 = 0, op2 = 0;
	char *kwlist[] = {
				"tid",
				"op1",
				"op2",
				NULL

		};

	//Initialize superclass and parse arguments
	if(PyLayerHeaderType.tp_init((PyObject *)self, args, kwds) < 0 ||
			!PyArg_ParseTupleAndKeywords(args, kwds, "|bbb", kwlist,
					&tid, &op1, &op2))
		return -1;

	self->tid = tid;
	self->op1 = op1;
	self->op2 = op2;

	return 0;
}

static int
PyLMPHdr_traverse(PyLMPHdr *self, visitproc visit, void *arg)
{
	return PyLayerHeaderType.tp_traverse((PyObject *) self, visit, arg);
}

static int
PyLMPHdr_clear(PyLMPHdr *self)
{
	return PyLayerHeaderType.tp_clear((PyObject *) self);
}

static void
PyLMPHdr_dealloc(PyLMPHdr *self)
{
	PyLayerHeaderType.tp_dealloc((PyObject *) self);
}

/**
 * Generate a Python tuple, left->right is MSB->LSB
 */
static PyObject *
PyLMPHdr_getrawdata(PyLMPHdr *self, void *closure)
{
	uint8_t byte0 = self->op1 << LMP_OP1_SHIFT |
					(self->tid & LMP_TID_MASK);

	if(self->op1 >=124 && self->op1 <= 127) {
		return Py_BuildValue("(BB)", byte0, self->op2);
	}
	return Py_BuildValue("(B)", byte0);
}

static PyGetSetDef PyLMPHdr_getseters[] = {
		{ "rawdata",
			(getter) PyLMPHdr_getrawdata,
			NULL,
			"The data in tuple representation.",
			NULL
		},
		{NULL}
};

static PyMemberDef PyLMPHdr_members[] = {
		{"tid", T_UBYTE, offsetof(PyLMPHdr, tid), 0, "Tid"},
		{"op1", T_UBYTE, offsetof(PyLMPHdr, op1), 0, "Opcode 1"},
		{"op2", T_UBYTE, offsetof(PyLMPHdr, op2), 0, "Opcode 2"},
		{NULL}
};

PyTypeObject PyLMPHdrType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btlayers.LMPHeader",         /*tp_name*/
		sizeof(PyLMPHdr),      /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor) PyLMPHdr_dealloc,	/*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		0, 							/*tp_repr*/
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
		"LMP header type.",      /* tp_doc */
		(traverseproc) PyLMPHdr_traverse,  /* tp_traverse */
		(inquiry) PyLMPHdr_clear,       /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,    			         /* tp_methods */
		PyLMPHdr_members,        	/* tp_members */
		PyLMPHdr_getseters,        /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	    (initproc)PyLMPHdr_init,      	/* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};


/**
 * L2CAP Header
 */

static int
PyL2CAPHdr_init(PyL2CAPHdr *self, PyObject *args, PyObject *kwds)
{
	int length = 0,chan_id = 0;
	char *kwlist[] = {
				"length",
				"chanid",
				NULL

		};

	//Initialize superclass and parse arguments
	if(PyLayerHeaderType.tp_init((PyObject *)self, args, kwds) < 0 ||
			!PyArg_ParseTupleAndKeywords(args, kwds, "ii", kwlist,
					&length, &chan_id))
		return -1;

	//Do overflow checking before assigning to members
	if(length < 0 || chan_id < 0 || length > MAX_UINT16 || chan_id > MAX_UINT16)
		return -1;
	else{
		self->length = (uint16_t) length;
		self->chan_id = (uint16_t) chan_id;
	}

	return 0;
}

static int
PyL2CAPHdr_traverse(PyL2CAPHdr *self, visitproc visit, void *arg)
{
	return PyLayerHeaderType.tp_traverse((PyObject *) self, visit, arg);
}

static int
PyL2CAPHdr_clear(PyL2CAPHdr *self)
{
	return PyLayerHeaderType.tp_clear((PyObject *) self);
}

static void
PyL2CAPHdr_dealloc(PyL2CAPHdr *self)
{
	PyLayerHeaderType.tp_dealloc((PyObject *) self);
}

/**
 * Generate a Python string, left->right is MSB->LSB
 */
static PyObject *
PyL2CAPHdr_getrawdata(PyL2CAPHdr *self, void *closure)
{

	return Py_BuildValue("(BBBB)", self->chan_id >> BYTE_BITLEN,
								   self->chan_id & (255),
								   self->length >> BYTE_BITLEN,
								   self->length & (255 ));

}

static PyGetSetDef PyL2CAPHdr_getseters[] = {
		{ "rawdata",
			(getter) PyL2CAPHdr_getrawdata,
			NULL,
			"The data in string representation. We can use struct module to unpack",
			NULL
		},
		{NULL}
};

static PyMemberDef PyL2CAPHdr_members[] = {
		{"length", T_USHORT, offsetof(PyL2CAPHdr, length), 0, "Length excluding header"},
		{"chan_id", T_USHORT, offsetof(PyL2CAPHdr, chan_id), 0, "Channel ID"},
		{NULL}
};

PyTypeObject PyL2CAPHdrType =  {
	   PyObject_HEAD_INIT(NULL)
		0,                         /*ob_size*/
		"btlayers.L2CAPHeader",         /*tp_name*/
		sizeof(PyL2CAPHdr),      /*tp_basicsize*/
		0,                         /*tp_itemsize*/
		(destructor) PyL2CAPHdr_dealloc,	/*tp_dealloc*/
		0,                         /*tp_print*/
		0,                         /*tp_getattr*/
		0,                         /*tp_setattr*/
		0,                         /*tp_compare*/
		0, 							/*tp_repr*/
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
		"LMP header type.",      /* tp_doc */
		(traverseproc) PyL2CAPHdr_traverse,  /* tp_traverse */
		(inquiry) PyL2CAPHdr_clear,       /* tp_clear */
		0,                          /* tp_richcompare */
		0,                          /* tp_weaklistoffset */
		0,                          /* tp_iter */
		0,                          /* tp_iternext */
		0,    			         /* tp_methods */
		PyL2CAPHdr_members,        	/* tp_members */
		PyL2CAPHdr_getseters,        /* tp_getset */
		0,                         /* tp_base */
		0,                         /* tp_dict */
		0,                         /* tp_descr_get */
		0,                         /* tp_descr_set */
		0,                         /* tp_dictoffset */
	    (initproc)PyL2CAPHdr_init,      	/* tp_init */
		0,                         /* tp_alloc */
		0,                 /* tp_new */
};



PyMODINIT_FUNC
initbtlayers(void)
{

	PyObject *m;

	PyLayerHeaderType.tp_base = &PyRawObjectType;
	PyLayerUnitType.tp_base = &PyRawObjectType;
	PyLMPHdrType.tp_base = &PyLayerHeaderType;
	PyL2CAPHdrType.tp_base = &PyLayerHeaderType;

	if(PyType_Ready(&PyRawObjectType) < 0 ||
			PyType_Ready(&PyLayerHeaderType) < 0 ||
			PyType_Ready(&PyLayerUnitType)  < 0 ||
			PyType_Ready(&PyLMPHdrType) < 0||
			PyType_Ready(&PyL2CAPHdrType) < 0)
		return;

	m = Py_InitModule3("btlayers", NULL, "Bluetooth layer data types.");
	if (m == NULL)
	{
		return;
	}

	Py_INCREF(&PyRawObjectType);
	Py_INCREF(&PyLayerHeaderType);
	Py_INCREF(&PyLayerUnitType);
	Py_INCREF(&PyLMPHdrType);
	Py_INCREF(&PyL2CAPHdrType);
	PyModule_AddObject(m, "BtRaw", (PyObject *) &PyRawObjectType);
	PyModule_AddObject(m, "BtLayerHeader", (PyObject *) &PyLayerHeaderType);
	PyModule_AddObject(m, "BtLayerUnit", (PyObject *) &PyLayerUnitType);
	PyModule_AddObject(m, "LMPHeader", (PyObject *) &PyLMPHdrType);
	PyModule_AddObject(m, "L2CAPHeader", (PyObject *) &PyL2CAPHdrType);

}
