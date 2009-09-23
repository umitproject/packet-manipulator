

#include "layers.h"
#include <string.h>
#include "structmember.h"


	/**
	 * To be overwritten for implementations of PyRawObject
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
		PyString_Concat(&data_repr,  obj->rawdata->ob_type->tp_repr(obj->rawdata));
		return data_repr;
	}

	static int
	PyRawObject_traverse(PyRawObject *self, visitproc visit, void *arg)
	{
		Py_VISIT(self->rawdata);
		return 0;
	}

	static int
	PyRawObject_clear(PyRawObject *self)
	{
		PyObject *tmp;
		tmp = self->rawdata;
		self->rawdata = NULL;
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
		if(self != NULL){
			self->rawdata = PyList_New(0);
		}
		Py_INCREF(self->rawdata);
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
			{"rawdata", T_OBJECT, offsetof(PyRawObject, rawdata), 0, PyDoc_STR("Data attribute.")},
			{NULL}
	};

	PyTypeObject PyRawObjectType =  {
		   PyObject_HEAD_INIT(NULL)
			0,                         			/*ob_size*/
			"btlayers.BtRaw",             		/*tp_name*/
			sizeof(PyRawObject),             	/*tp_basicsize*/
			0,                         			/*tp_itemsize*/
			(destructor) PyRawObject_dealloc, 	/*tp_dealloc*/
			0,                         			/*tp_print*/
			0,                         			/*tp_getattr*/
			0,                         			/*tp_setattr*/
			0,                         			/*tp_compare*/
			(reprfunc) PyRawObject_repr, 		/*tp_repr*/
			0,                         			/*tp_as_number*/
			0,                         			/*tp_as_sequence*/
			0,                         			/*tp_as_mapping*/
			0,                         			/*tp_hash */
			0,                         			/*tp_call*/
			0,                         			/*tp_str*/
			0,                         			/*tp_getattro*/
			0,                         			/*tp_setattro*/
			0,                         			/*tp_as_buffer*/
			Py_TPFLAGS_DEFAULT |
			Py_TPFLAGS_BASETYPE |
			Py_TPFLAGS_HAVE_GC,					/*tp_flags*/
			"Raw Bluetooth object.",    		/* tp_doc */
			(traverseproc)PyRawObject_traverse, /* tp_traverse */
			(inquiry)PyRawObject_clear,         /* tp_clear */
			0,                          		/* tp_richcompare */
			0,                          		/* tp_weaklistoffset */
			0,                          		/* tp_iter */
			0,                          		/* tp_iternext */
			0,    			         			/* tp_methods */
			PyRawObject_members,             	/* tp_members */
			0,                         			/* tp_getset */
			0,                         			/* tp_base */
			0,                         			/* tp_dict */
			0,                         			/* tp_descr_get */
			0,                         			/* tp_descr_set */
			0,                         			/* tp_dictoffset */
		   (initproc)PyRawObject_init,      	/* tp_init */
			0,                         			/* tp_alloc */
			PyRawObject_new,                 	/* tp_new */
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

	static PyObject *
	PyLayerHeader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
	{
		return PyRawObjectType.tp_new(type, args, kwds);
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
		return PyList_New(0);
	}

	static PyGetSetDef PyLayerHeader_getseters[] =  {
			{"rawdata", (getter) PyLayerHeader_getdata,
					NULL, "Get raw data for header in list representation."
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
			PyLayerHeader_new,                 						/* tp_new */
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

		if(!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", kwlist,
				&self->hdr, &self->payload))
			return -1;

		if(self->hdr == NULL)
		{
			self->hdr = (PyLayerHeader *) PyLayerHeaderType.tp_new(&PyLayerHeaderType, NULL, NULL);
			if(PyLayerHeaderType.tp_init((PyObject *) self->payload, NULL, NULL) < 0)
				return -1;
			Py_INCREF(self->hdr);
		}

		if(self->payload == NULL)
		{
			self->payload = (PyRawObject *) PyRawObjectType.tp_new(&PyRawObjectType, NULL, NULL);
			if(PyRawObjectType.tp_init((PyObject *)self->payload, NULL, NULL) < 0)
				return -1;
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
				&& PySequence_Check(hdrraw))
		{
			if(self->payload != (PyRawObject *)Py_None &&
				(payloadraw = PyObject_GetAttrString((PyObject *)self->payload, "rawdata")) != NULL
				&& PySequence_Check(payloadraw))
			{
				ret = PySequence_Concat(hdrraw, payloadraw);
			}
			else if(self->payload == (PyRawObject *) Py_None)
			{
				ret = hdrraw;
			}
		}


		//TODO: Do error setting here

		return ret;
	}

	static PyGetSetDef PyLayerUnit_getseters[] =  {
			{"rawdata", (getter) PyLayerUnit_getdata,
						NULL,
						"Data in list representation.",
						NULL
			},
			{NULL}
	};

	static PyMemberDef PyLayerUnit_members[] =  {
			{ "header", T_OBJECT, offsetof(PyLayerUnit, hdr), 0, "Header."},
			{ "payload", T_OBJECT, offsetof(PyLayerUnit, payload), 0, "Payload."},
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
			PyLayerUnit_members,	/* tp_members */
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

	static PyObject *
	PyLMPHdr_getrawdata(PyLMPHdr *self, void *closure)
	{
		uint8_t byte0 = self->op1 << LMP_OP1_SHIFT |
						(self->tid & LMP_TID_MASK);

		if(self->op1 >=124 && self->op1 <= 127) {
			return Py_BuildValue("[BB]", byte0, self->op2);
		}
		return Py_BuildValue("[B]", byte0);
	}

	static PyGetSetDef PyLMPHdr_getseters[] = {
			{ "rawdata",
				(getter) PyLMPHdr_getrawdata,
				NULL,
				"The data in list representation.",
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
					"chan_id",
					NULL

			};

		//Initialize superclass and parse arguments
		if(PyLayerHeaderType.tp_init((PyObject *)self, args, kwds) < 0 ||
				!PyArg_ParseTupleAndKeywords(args, kwds, "|ii", kwlist,
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

		return Py_BuildValue("[BBBB]", 	self->length >> BYTE_BITLEN ,
										self-> length & MAX_UINT8,
										self->chan_id >> BYTE_BITLEN,
										self->chan_id & MAX_UINT8);

	}

	static PyGetSetDef PyL2CAPHdr_getseters[] = {
			{ "rawdata",
				(getter) PyL2CAPHdr_getrawdata,
				NULL,
				"The data in list representation.",
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
			"L2CAP basic header type.",      /* tp_doc */
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

	/**
	 * Lastly for the sniffing components
	 */

	/*
	 * The constructor does no overflow checking
	 */
	static int
	PySniffHdr_init(PySniffHdr *self, PyObject *args, PyObject *kwds)
	{
		uint8_t hlen = 0, hdr0 = 0, chan = 0, seq_num = 0;
		uint16_t dlen = 0;
		uint32_t clock = 0, timer = 0 ;
		char *kwlist[] = {
				"header_len",
				"clock",
				"hdr0",
				"dlen",
				"timer",
				"channel",
				"seq_num",
				NULL
			};
		//Initialize superclass and parse arguments
		if(PyLayerHeaderType.tp_init((PyObject *)self, args, kwds) < 0 ||
				!PyArg_ParseTupleAndKeywords(args, kwds, "|BIBHIBB", kwlist,
						&hlen, &clock, &hdr0, &dlen, &timer, &chan, &seq_num))
			return -1;
		//Assign default values
		self->hlen = hlen;
		self->hdr0 = hdr0;
		self->dlen = dlen;
		self->timer = timer;
		self->clock = clock;
		self->chan = chan;
		self->seq = seq_num;

		return 0;
	}

	static PyObject *
	PySniffHdr_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
	{
		return PyLayerHeaderType.tp_new(type, args, kwds);
	}

	static int
	PySniffHdr_traverse(PySniffHdr *self, visitproc visit, void *arg)
	{
		return PyLayerHeaderType.tp_traverse((PyObject *) self, visit, arg);
	}

	static int
	PySniffHdr_clear(PySniffHdr *self)
	{
		return PyLayerHeaderType.tp_clear((PyObject *) self);
	}

	static void
	PySniffHdr_dealloc(PySniffHdr *self)
	{
		PyLayerHeaderType.tp_dealloc((PyObject *) self);
	}

	static PyObject *
	PySniffHdr_getrawdata(PySniffHdr *self, void *closure)
	{
		char fmtstr[self->hlen + 2 + 1], *fp = fmtstr + 1; // + 2 parentheses + 1 null char
		fmtstr[self->hlen + 2]  = '\0';
		fmtstr[0] = '['; fmtstr[self->hlen + 1] = ']';
		memset(fp, 'B', self->hlen);

		return Py_BuildValue(fmtstr,	self->hlen,
										self->clock >> (3 * BYTE_BITLEN),
										(self->clock >> (2 * BYTE_BITLEN)) & MAX_UINT8,
										(self->clock >> BYTE_BITLEN) & MAX_UINT8,
										(self->clock & MAX_UINT8),
										self->hdr0,
										(self->dlen >> (2 * BYTE_BITLEN)) & MAX_UINT8,
										(self->dlen & MAX_UINT8),
										(self->timer >> (3 * BYTE_BITLEN)),
										(self->timer >> (2 * BYTE_BITLEN)) & MAX_UINT8,
										(self->timer >> (1 * BYTE_BITLEN)) & MAX_UINT8,
										self->timer & MAX_UINT8,
										self->chan,
										self->seq);

	}

	static PyGetSetDef PySniffHdr_getseters[] = {
			{ "rawdata",
				(getter) PySniffHdr_getrawdata,
				NULL,
				"The data in list representation.",
				NULL
			},
			{NULL}
	};

	static PyMemberDef PySniffHdr_members[] = {
			{"header_len", T_UBYTE, offsetof(PySniffHdr, hlen), 0, "Header length."},
			{"clock", T_UINT, offsetof(PySniffHdr, clock), 0, "Clock value."},
			{"header_byte0", T_UBYTE, offsetof(PySniffHdr, hdr0), 0, "Value of byte 0 of Bluetooth packet header"},
			{"sniff_len", T_USHORT, offsetof(PySniffHdr, dlen), 0, "Sniff length."},
			{"timer", T_UINT, offsetof(PySniffHdr, timer), 0, "Timer value."},
			{"chan", T_UBYTE, offsetof(PySniffHdr, chan), 0, "Channel number."},
			{"seq_num", T_UBYTE, offsetof(PySniffHdr, seq), 0, "Sequence number."},
			{NULL}
	};

	PyTypeObject PySniffHdrType =  {
		   PyObject_HEAD_INIT(NULL)
			0,                         /*ob_size*/
			"btlayers.BtSniffHeader",         /*tp_name*/
			sizeof(PySniffHdr),      /*tp_basicsize*/
			0,                         /*tp_itemsize*/
			(destructor) PySniffHdr_dealloc,	/*tp_dealloc*/
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
			"Frontline packet header.",      /* tp_doc */
			(traverseproc) PySniffHdr_traverse,  /* tp_traverse */
			(inquiry) PySniffHdr_clear,       /* tp_clear */
			0,                          /* tp_richcompare */
			0,                          /* tp_weaklistoffset */
			0,                          /* tp_iter */
			0,                          /* tp_iternext */
			0,    			         /* tp_methods */
			PySniffHdr_members,        	/* tp_members */
			PySniffHdr_getseters,        /* tp_getset */
			0,                         /* tp_base */
			0,                         /* tp_dict */
			0,                         /* tp_descr_get */
			0,                         /* tp_descr_set */
			0,                         /* tp_dictoffset */
			(initproc)PySniffHdr_init,      	/* tp_init */
			0,                         /* tp_alloc */
			PySniffHdr_new,                 /* tp_new */
	};


	//Does no type checking. Should implement?
	static int
	PySniffRaw_init(PySniffRaw *self, PyObject *args, PyObject *kwds)
	{
		return PyLayerUnitType.tp_init((PyObject *)self, args, kwds);
	}

	static PyObject *
	PySniffRaw_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
	{
		return PyLayerUnitType.tp_new(type, args, kwds);
	}

	static int
	PySniffRaw_traverse(PySniffRaw *self, visitproc visit, void *arg)
	{
		return PyLayerUnitType.tp_traverse((PyObject *) self, visit, arg);
	}

	static int
	PySniffRaw_clear(PySniffRaw *self)
	{
		return PyLayerHeaderType.tp_clear((PyObject *) self);
	}

	static void
	PySniffRaw_dealloc(PySniffRaw *self)
	{
		PyLayerHeaderType.tp_dealloc((PyObject *) self);
	}

	static PyObject *
	PySniffRaw_getllid(PySniffRaw *self, void *closure)
	{
		PySniffHdr *hdr = (PySniffHdr *)self->raw.hdr;
		return Py_BuildValue("I", (hdr->dlen >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK);
	}

	static PyObject *
	PySniffRaw_getis_src_master(PySniffRaw *self, void *closure)
	{
		PySniffHdr *hdr = (PySniffHdr *) self->raw.hdr;

		if(!(hdr->clock & FP_SLAVE_MASK))
			Py_RETURN_TRUE;
		Py_RETURN_FALSE;
	}

	static PyObject *
	PySniffRaw_gettype(PySniffRaw *self, void *closure)
	{
		PySniffHdr  *hdr = (PySniffHdr *)self->raw.hdr;
		if(!hdr)
			return NULL;
		return Py_BuildValue("I", (hdr->hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK);
	}

	static PyObject *
	PySniffRaw_getaddress(PySniffRaw *self, void *closure)
	{
		PySniffHdr *hdr = (PySniffHdr *)self->raw.hdr;
		if(!hdr)
			return NULL;
		return Py_BuildValue("I", hdr->hdr0 & FP_ADDR_MASK);
	}

	static PyObject *
	PySniffRaw_getstatus(PySniffRaw *self, void *closure)
	{
		PySniffHdr *hdr = (PySniffHdr *)self->raw.hdr;
		if(!hdr)
			return NULL;
		return Py_BuildValue("I", hdr->clock >> FP_STATUS_SHIFT);
	}

	static PyObject *
	PySniffRaw_getpayloadlen(PySniffRaw *self, void *closure)
	{
		PySniffHdr *hdr = (PySniffHdr *)self->raw.hdr;
		if(!hdr)
			return NULL;
		return Py_BuildValue("I", hdr->dlen >> FP_LEN_SHIFT);
	}


	static PyObject *
	PySniffRaw_getheader_attribs(PySniffRaw *self, void *closure)
	{
		return PyObject_GetAttrString((PyObject *)self->raw.hdr, (char *) closure);
	}

	static PyGetSetDef PySniffRaw_getseters[] = {
			{ 	"llid",
				(getter) PySniffRaw_getllid,
				NULL,
				"LLID.",
				NULL
			},
			{ 	"is_src_master",
				(getter) PySniffRaw_getis_src_master,
				NULL,
				"True if source is master device, false otherwise.",
				NULL
			},
			{ 	"type",
				(getter) PySniffRaw_gettype,
				NULL,
				"Type (e.g. DV)",
				NULL
			},
			{ 	"address",
				(getter) PySniffRaw_getaddress,
				NULL,
				"Piconet address",
				NULL
			},
			{ 	"status",
				(getter) PySniffRaw_getstatus,
				NULL,
				"Status",
				NULL
			},

			{ 	"header_len",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Header length",
				"header_len"
			},
			{ 	"clock",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Clock",
				"clock"
			},
			{ 	"header_byte0",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"First byte of bluetooth header.",
				"header_byte0"
			},
			{ 	"sniff_len",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Sniff Length as specified by Frontline.",
				"sniff_len"
			},
			{ 	"payload_len",
				(getter) PySniffRaw_getpayloadlen,
				NULL,
				"Payload length.",
				NULL
			},
			{ 	"timer",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Timer.",
				"timer"
			},
			{ 	"chan",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Channel.",
				"chan"
			},
			{ 	"seq_num",
				(getter) PySniffRaw_getheader_attribs,
				NULL,
				"Sequence number.",
				"seq_num"
			},
			{NULL}
	};


	PyTypeObject PySniffRawType =  {
		   PyObject_HEAD_INIT(NULL)
			0,                         /*ob_size*/
			"btlayers.BtSniffUnit",         /*tp_name*/
			sizeof(PySniffRaw),      /*tp_basicsize*/
			0,                         /*tp_itemsize*/
			(destructor) PySniffRaw_dealloc,	/*tp_dealloc*/
			0,                         /*tp_print*/
			0, 							/*tp_getattr*/
			0,                         /*tp_setattr*/
			0,                         /*tp_compare*/
			0, 							/*tp_repr*/
			0,                         /*tp_as_number*/
			0,                         /*tp_as_sequence*/
			0,                         /*tp_as_mapping*/
			0,                         /*tp_hash */
			0,                         /*tp_call*/
			0,                         /*tp_str*/
			0,
			//(getattrofunc) PySniffRaw_getattr,  /*tp_getattro*/
			0,                         /*tp_setattro*/
			0,                         /*tp_as_buffer*/
			Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
			"Frontline packet.",      /* tp_doc */
			(traverseproc) PySniffRaw_traverse,  /* tp_traverse */
			(inquiry) PySniffRaw_clear,       /* tp_clear */
			0,                          /* tp_richcompare */
			0,                          /* tp_weaklistoffset */
			0,                          /* tp_iter */
			0,                  	     /* tp_iternext */
			0,    				         /* tp_methods */
			0,							/* tp_members */
			PySniffRaw_getseters,        /* tp_getset */
			0,                         /* tp_base */
			0,                         /* tp_dict */
			0,                         /* tp_descr_get */
			0,                         /* tp_descr_set */
			0,                         /* tp_dictoffset */
			(initproc)PySniffRaw_init,      	/* tp_init */
			0,                         /* tp_alloc */
			PySniffRaw_new,                 /* tp_new */
	};

	int setup_layer_types(void) {

		PyLayerHeaderType.tp_base = &PyRawObjectType;
		PyLayerUnitType.tp_base = &PyRawObjectType;
		PyLMPHdrType.tp_base = &PyLayerHeaderType;
		PyL2CAPHdrType.tp_base = &PyLayerHeaderType;
		PySniffHdrType.tp_base = &PyLayerHeaderType;
		PySniffRawType.tp_base = &PyLayerUnitType;

		if(PyType_Ready(&PyRawObjectType) < 0
				|| PyType_Ready(&PyLayerHeaderType) < 0
				|| PyType_Ready(&PyLayerUnitType)  < 0
				|| PyType_Ready(&PyLMPHdrType) < 0
				|| PyType_Ready(&PyL2CAPHdrType) < 0
				|| PyType_Ready(&PySniffHdrType) < 0
				|| PyType_Ready(&PySniffRawType) < 0
		)
			return -1;

		Py_INCREF(&PyRawObjectType);
		Py_INCREF(&PyLayerHeaderType);
		Py_INCREF(&PyLayerUnitType);
		Py_INCREF(&PyLMPHdrType);
		Py_INCREF(&PyL2CAPHdrType);
		Py_INCREF(&PySniffHdrType);
		Py_INCREF(&PySniffRawType);

		return 0;
	}

	PyMODINIT_FUNC
	initbtlayers(void)
	{

		PyObject *m;

		if(setup_layer_types() < 0)
			return;

		m = Py_InitModule3("btlayers", NULL, "Bluetooth layer data types.");
		if (m == NULL)
		{
			return;
		}

		PyModule_AddObject(m, "BtRaw", (PyObject *) &PyRawObjectType);
		PyModule_AddObject(m, "BtLayerHeader", (PyObject *) &PyLayerHeaderType);
		PyModule_AddObject(m, "BtLayerUnit", (PyObject *) &PyLayerUnitType);
		PyModule_AddObject(m, "LMPHeader", (PyObject *) &PyLMPHdrType);
		PyModule_AddObject(m, "L2CAPHeader", (PyObject *) &PyL2CAPHdrType);
		PyModule_AddObject(m, "BtSniffHeader", (PyObject *) &PySniffHdrType);
		PyModule_AddObject(m, "BtSniffUnit", (PyObject *) &PySniffRawType);
	}
