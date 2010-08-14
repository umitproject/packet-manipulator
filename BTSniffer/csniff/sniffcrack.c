/*
 * sniffcrack.c
 *
 *  Created on: Jul 21, 2009
 *      Author: qsy
 */

#include <error.h>
#include "btconstants.h"
#include "basesniffmodule.h"
#include "sniffcrack.h"

#define DEBUG

static void debug_print(char *s)
{
#ifdef DEBUG
		printf("%s\n", s);
#endif
}

/**
 * This section for pincracking.
 */
static int
listcopy(PyObject *srclist, PyObject *destlist)
{
	PyObject *tmp;
	int i;

	if(!PyList_Check(srclist) || !PyList_Check(destlist))
		return 0;

	for(i = 0 ; i < PyList_Size(srclist); i++)
	{
		tmp = PyList_GetItem(destlist, i);
		PyList_SetItem(destlist, i, PyList_GetItem(srclist, i));
		Py_XDECREF(tmp);
	}

	return -1;
}

static PyObject *
_sniffcrack_setpindata(PyObject *dummy, PyObject *args, PyObject *kwds)
//_sniffcrack_setpindata(PyState *s, int op, void *buf, int len)
{
	int op;
	PyObject *list_buf, *src_is_master;
	PyState *s;

	char *kwlist[] = { "state",
			"op",
			"datalist",
			"src_is_master",
			NULL
	};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "OiOO", kwlist, &s,
			&op, &list_buf, &src_is_master)){
		return NULL;
	}

	switch (op) {
		case LMP_IN_RAND:
			s->s_pin = 1 | GOT_IN_RAND;
			//			s->s_pin_master = s->s_master;
			debug_print("in_rand");
			//memcpy(s->s_pin_data[0], buf, len);
			if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 0)))
				return NULL;
			break;

		case LMP_COMB_KEY:
			if (!(s->s_pin & GOT_IN_RAND)){
				debug_print("missed in_rand");
				RETURN_VOID
			}

			//if (s->s_master == s->s_pin_master) {
			if(src_is_master == Py_True){
				//memcpy(s->s_pin_data[1], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 1)))
					return NULL;
				debug_print("got comb1");
				s->s_pin |= GOT_COMB1;

			} else {
				//memcpy(s->s_pin_data[2], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 2)))
					return NULL;
				debug_print("got comb2");
				s->s_pin |= GOT_COMB2;

			}
			break;

		case LMP_AU_RAND:
			if ((!(s->s_pin & GOT_COMB1))
				|| (!(s->s_pin & GOT_COMB2)))
			{
				debug_print("missed comb1 or comb2");
				RETURN_VOID
			}


			//if (s->s_master == s->s_pin_master) {
			if(src_is_master == Py_True) {
				//memcpy(s->s_pin_data[3], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 3)))
					return NULL;
				s->s_pin |= GOT_AU_RAND1;
				debug_print("got au rand 1");

			} else {
				//memcpy(s->s_pin_data[4], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 4)))
						return NULL;
				s->s_pin |= GOT_AU_RAND2;
				debug_print("got au rand 2");
			}
			break;

		case LMP_SRES:

			if(src_is_master == Py_False) {
			//if (s->s_master != s->s_pin_master) {
				if (!(s->s_pin & GOT_AU_RAND1))
				{
					debug_print("missed au rand 1");
					RETURN_VOID
				}
				//memcpy(s->s_pin_data[6], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 6)))
					return NULL;
				debug_print("got sres1");
				s->s_pin |= GOT_SRES1;

			} else {
				if (!(s->s_pin & GOT_AU_RAND2)){
					debug_print("missed au rand 2");
					RETURN_VOID
				}
				//memcpy(s->s_pin_data[5], buf, len);
				if(!listcopy(list_buf, PyList_GetItem(s->s_pindata, 5)))
					return NULL;
				debug_print("got sres2");
				s->s_pin |= GOT_SRES2;
			}
			break;

		default:
			RETURN_VOID
	}
	RETURN_VOID
}


static PyMethodDef sniffcrack_methods[] = {
		{"_setpindata", (PyCFunction)_sniffcrack_setpindata, METH_VARARGS | METH_KEYWORDS,
				"Does the computation in preparation for pincrack. Computation state saved in State object" },
		{NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
init_crack(void)
{
	PyObject *m;
	m = Py_InitModule3("_crack", sniffcrack_methods, "Module contains pincracking, etc");
	if(m == NULL) return;
}
