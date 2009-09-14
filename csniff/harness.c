
#include <Python.h>
#include "harness.h"
#include "layers.h"
#include "btconstants.h"
#include "structmember.h"

//Added just for convenience
static void show(const char *text)
{
	printf("%s\n", text);
}

static PyObject *
harness_testLMPHdrMethods(PyObject *dummy, PyObject *args, PyObject *kwds)
{
	PyLMPHdr *hdr;
	show("Test LMP Header");
	hdr = (PyLMPHdr *) PyLMPHdrType.tp_new(&PyLMPHdrType, NULL, NULL);
	if (PyLMPHdrType.tp_init((PyObject *)hdr, PyTuple_New(0), PyDict_New()) < 0)
		return NULL;
	show("Test LMP Header OK");
	RETURN_VOID
}

static PyObject *
harness_testRawObjectMethods(PyObject *dummy, PyObject *args, PyObject *kwds)
{

	PyRawObject *raw;
	raw = (PyRawObject *) PyRawObjectType.tp_new(&PyRawObjectType, NULL, NULL);
	show("Raw Object Test");
	if(PyRawObjectType.tp_init((PyObject *)raw, NULL, NULL) < 0)
	{
		return NULL;
	}
	//Test that the list works
	if(!PyList_Check(raw->rawdata)){
		show("Not list!");
	}

	show("RawObject OK");

	RETURN_VOID
}

static PyObject *
harness_testSniffHdrMethods(PyObject *self, PyObject *args, PyObject *kwds)
{
	PySniffHdr *hdr;
	show("New SniffHdr. See how this works out.");
	hdr = (PySniffHdr *) PySniffHdrType.tp_new(&PySniffHdrType, args, kwds);
	show("New sniffHdr works");
	if(PySniffHdrType.tp_init((PyObject *)hdr, PyTuple_New(0), PyDict_New()) < 0)
		return NULL;
	show("SniffHeader OK");
	RETURN_VOID
}

static PyObject *
harness_testLayerUnitMethods(PyObject *self, PyObject *args, PyObject *kwds)
{
	PyLayerUnit *unit;
	PyObject *tmp;

	show("New LayerUnit");
	unit = (PyLayerUnit *)PyLayerUnitType.tp_new(&PyLayerUnitType, args, kwds);
	if (PyLayerUnitType.tp_init((PyObject *)unit, PyTuple_New(0), PyDict_New()) < 0)
		return NULL;

	show("Getting raw data");
	tmp = PyObject_GetAttrString((PyObject *)unit, "rawdata");
	show("LayerUnit OK");
	RETURN_VOID
}

static PyObject *
harness_testSniffRawMethods(PyObject *self, PyObject *args, PyObject *kwds)
{
	PySniffRaw *raw;
	PySniffHdr *hdr;
	PyObject *tmp;

	hdr = (PySniffHdr *) PySniffHdrType.tp_new(&PySniffHdrType, args, kwds);
	if(PySniffHdrType.tp_init((PyObject *)hdr, PyTuple_New(0), PyDict_New()) < 0)
		return NULL;

	show("New SniffRaw.");
	raw = (PySniffRaw *) PySniffRawType.tp_new(&PySniffRawType, args, kwds);
	if(PySniffRawType.tp_init((PyObject *)raw, PyTuple_New(0), PyDict_New()) < 0)  { //this should initialize its header
		show("Init error");
		return NULL;
	}

	if(&raw->raw == NULL) {
		show("raw is null");
		return NULL;
	}

	if(raw->raw.hdr == NULL)  {
		show("header is null");
		return NULL;
	}

	if(raw->raw.payload == NULL)
	{
		show("payload is null");
		return NULL;
	}

	show("Getting rawdata from raw");
	tmp = PyObject_GetAttrString((PyObject *)raw, "rawdata");

	show("SniffRaw OK");
	RETURN_VOID
}


static PyObject *
harness_testParseArg(PyObject *self, PyObject *args, PyObject *kwds)
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
	if (!PyArg_ParseTupleAndKeywords(PyTuple_New(0), PyDict_New(), "|BIBHIBB", kwlist,
			&hlen, &clock, &hdr0, &dlen, &timer, &chan, &seq_num))
	{
		show("ParseArg Fail");
		return NULL;
	}
	show("ParseArg OK");
	RETURN_VOID
}


static PyMethodDef harness_methods[] =  {

		{	"test_sniff_header", (PyCFunction)harness_testSniffHdrMethods, METH_NOARGS,
			"Testing of SniffHdrType"
		},
		{	"test_parsearg", (PyCFunction) harness_testParseArg, METH_VARARGS | METH_KEYWORDS,
			"NULL"
		},
		{	"test_sniff_raw", (PyCFunction)harness_testSniffRawMethods, METH_NOARGS,
					"Testing of SniffRaw"
		},
		{	"test_raw", (PyCFunction)harness_testRawObjectMethods, METH_NOARGS,
			"Testing of RawObject"
		},
		{	"test_lmp_header", (PyCFunction)harness_testLMPHdrMethods, METH_NOARGS,
			"Testing of LMPHdr"
		},
		{	"test_layer_unit", (PyCFunction)harness_testLayerUnitMethods, METH_NOARGS,
			"Testing of LayerUnit"
		},
		{NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
initharness(void)
{
	PyObject *m;

	show("Harness test.");
	setup_layer_types();
	m = Py_InitModule3("harness", harness_methods, "BTSniff Extension tests");

	if( m == NULL)
		return;

}
