/* -- THIS FILE IS GENERATED - DO NOT EDIT *//* -*- Mode: C; c-basic-offset: 4 -*- */

#include <Python.h>



#line 4 "moo.override"
#include <Python.h>
#define NO_IMPORT_PYGOBJECT
#include <pygobject.h>
#include <pygtk/pygtk.h>
#include "moobigpaned.h"
#line 14 "moo-pygtk.c"


/* ---------- types from other modules ---------- */
static PyTypeObject *_PyGtkObject_Type;
#define PyGtkObject_Type (*_PyGtkObject_Type)
static PyTypeObject *_PyGtkWidget_Type;
#define PyGtkWidget_Type (*_PyGtkWidget_Type)
static PyTypeObject *_PyGtkFrame_Type;
#define PyGtkFrame_Type (*_PyGtkFrame_Type)
static PyTypeObject *_PyGtkBin_Type;
#define PyGtkBin_Type (*_PyGtkBin_Type)
static PyTypeObject *_PyGdkPixbuf_Type;
#define PyGdkPixbuf_Type (*_PyGdkPixbuf_Type)


/* ---------- forward type declarations ---------- */
PyTypeObject G_GNUC_INTERNAL PyMooPaneLabel_Type;
PyTypeObject G_GNUC_INTERNAL PyMooPaneParams_Type;
PyTypeObject G_GNUC_INTERNAL PyMooBigPaned_Type;
PyTypeObject G_GNUC_INTERNAL PyMooPaned_Type;
PyTypeObject G_GNUC_INTERNAL PyMooPane_Type;

#line 37 "moo-pygtk.c"



/* ----------- MooPaneLabel ----------- */

static int
_wrap_moo_pane_label_new(PyGBoxed *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "icon_name", "icon_pixbuf", "label_text", "window_title", NULL };
    char *icon_name = NULL, *label_text = NULL, *window_title = NULL;
    PyGObject *py_icon_pixbuf = NULL;
    GdkPixbuf *icon_pixbuf = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"|zOzz:MooPaneLabel.__init__", kwlist, &icon_name, &py_icon_pixbuf, &label_text, &window_title))
        return -1;
    if ((PyObject *)py_icon_pixbuf == Py_None)
        icon_pixbuf = NULL;
    else if (py_icon_pixbuf && pygobject_check(py_icon_pixbuf, &PyGdkPixbuf_Type))
        icon_pixbuf = GDK_PIXBUF(py_icon_pixbuf->obj);
    else if (py_icon_pixbuf) {
        PyErr_SetString(PyExc_TypeError, "icon_pixbuf should be a GdkPixbuf or None");
        return -1;
    }
    self->gtype = MOO_TYPE_PANE_LABEL;
    self->free_on_dealloc = FALSE;
    self->boxed = moo_pane_label_new(icon_name, (GdkPixbuf *) icon_pixbuf, label_text, window_title);

    if (!self->boxed) {
        PyErr_SetString(PyExc_RuntimeError, "could not create MooPaneLabel object");
        return -1;
    }
    self->free_on_dealloc = TRUE;
    return 0;
}

static PyObject *
_wrap_moo_pane_label_copy(PyObject *self)
{
    MooPaneLabel *ret;

    
    ret = moo_pane_label_copy(pyg_boxed_get(self, MooPaneLabel));
    
    /* pyg_boxed_new handles NULL checking */
    return pyg_boxed_new(MOO_TYPE_PANE_LABEL, ret, TRUE, TRUE);
}

static PyObject *
_wrap_moo_pane_label_free(PyObject *self)
{
    
    moo_pane_label_free(pyg_boxed_get(self, MooPaneLabel));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static const PyMethodDef _PyMooPaneLabel_methods[] = {
    { "copy", (PyCFunction)_wrap_moo_pane_label_copy, METH_NOARGS,
      NULL },
    { "free", (PyCFunction)_wrap_moo_pane_label_free, METH_NOARGS,
      NULL },
    { NULL, NULL, 0, NULL }
};

PyTypeObject G_GNUC_INTERNAL PyMooPaneLabel_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "moo_stub.PaneLabel",                   /* tp_name */
    sizeof(PyGBoxed),          /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)0,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)0,       /* tp_getattr */
    (setattrfunc)0,       /* tp_setattr */
    (cmpfunc)0,           /* tp_compare */
    (reprfunc)0,             /* tp_repr */
    (PyNumberMethods*)0,     /* tp_as_number */
    (PySequenceMethods*)0, /* tp_as_sequence */
    (PyMappingMethods*)0,   /* tp_as_mapping */
    (hashfunc)0,             /* tp_hash */
    (ternaryfunc)0,          /* tp_call */
    (reprfunc)0,              /* tp_str */
    (getattrofunc)0,     /* tp_getattro */
    (setattrofunc)0,     /* tp_setattro */
    (PyBufferProcs*)0,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)0,     /* tp_traverse */
    (inquiry)0,             /* tp_clear */
    (richcmpfunc)0,   /* tp_richcompare */
    0,             /* tp_weaklistoffset */
    (getiterfunc)0,          /* tp_iter */
    (iternextfunc)0,     /* tp_iternext */
    (struct PyMethodDef*)_PyMooPaneLabel_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    (struct PyGetSetDef*)0,  /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)0,    /* tp_descr_get */
    (descrsetfunc)0,    /* tp_descr_set */
    0,                 /* tp_dictoffset */
    (initproc)_wrap_moo_pane_label_new,             /* tp_init */
    (allocfunc)0,           /* tp_alloc */
    (newfunc)0,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)0              /* tp_is_gc */
};



/* ----------- MooPaneParams ----------- */

static int
_wrap_moo_pane_params_new(PyGBoxed *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "window_position", "detached", "maximized", "keep_on_top", NULL };
    PyObject *py_window_position = Py_None;
    int detached = FALSE, maximized = FALSE, keep_on_top = FALSE;
    GdkRectangle window_position_rect = { 0, 0, 0, 0 }, *window_position;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"|Oiii:MooPaneParams.__init__", kwlist, &py_window_position, &detached, &maximized, &keep_on_top))
        return -1;
    if (py_window_position == Py_None)
        window_position = NULL;
    else if (pygdk_rectangle_from_pyobject(py_window_position, &window_position_rect))
        window_position = &window_position_rect;
    else
            return -1;
    self->gtype = MOO_TYPE_PANE_PARAMS;
    self->free_on_dealloc = FALSE;
    self->boxed = moo_pane_params_new(window_position, detached, maximized, keep_on_top);

    if (!self->boxed) {
        PyErr_SetString(PyExc_RuntimeError, "could not create MooPaneParams object");
        return -1;
    }
    self->free_on_dealloc = TRUE;
    return 0;
}

static PyObject *
_wrap_moo_pane_params_copy(PyObject *self)
{
    MooPaneParams *ret;

    
    ret = moo_pane_params_copy(pyg_boxed_get(self, MooPaneParams));
    
    /* pyg_boxed_new handles NULL checking */
    return pyg_boxed_new(MOO_TYPE_PANE_PARAMS, ret, TRUE, TRUE);
}

static const PyMethodDef _PyMooPaneParams_methods[] = {
    { "copy", (PyCFunction)_wrap_moo_pane_params_copy, METH_NOARGS,
      NULL },
    { NULL, NULL, 0, NULL }
};

static PyObject *
_wrap_moo_pane_params__get_window_position(PyObject *self, void *closure)
{
    GdkRectangle ret;

    ret = pyg_boxed_get(self, MooPaneParams)->window_position;
    return pyg_boxed_new(GDK_TYPE_RECTANGLE, &ret, TRUE, TRUE);
}

static PyObject *
_wrap_moo_pane_params__get_detached(PyObject *self, void *closure)
{
    int ret;

    ret = pyg_boxed_get(self, MooPaneParams)->detached;
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_pane_params__get_maximized(PyObject *self, void *closure)
{
    int ret;

    ret = pyg_boxed_get(self, MooPaneParams)->maximized;
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_pane_params__get_keep_on_top(PyObject *self, void *closure)
{
    int ret;

    ret = pyg_boxed_get(self, MooPaneParams)->keep_on_top;
    return PyBool_FromLong(ret);

}

static const PyGetSetDef moo_pane_params_getsets[] = {
    { "window_position", (getter)_wrap_moo_pane_params__get_window_position, (setter)0 },
    { "detached", (getter)_wrap_moo_pane_params__get_detached, (setter)0 },
    { "maximized", (getter)_wrap_moo_pane_params__get_maximized, (setter)0 },
    { "keep_on_top", (getter)_wrap_moo_pane_params__get_keep_on_top, (setter)0 },
    { NULL, (getter)0, (setter)0 },
};

PyTypeObject G_GNUC_INTERNAL PyMooPaneParams_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "moo_stub.PaneParams",                   /* tp_name */
    sizeof(PyGBoxed),          /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)0,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)0,       /* tp_getattr */
    (setattrfunc)0,       /* tp_setattr */
    (cmpfunc)0,           /* tp_compare */
    (reprfunc)0,             /* tp_repr */
    (PyNumberMethods*)0,     /* tp_as_number */
    (PySequenceMethods*)0, /* tp_as_sequence */
    (PyMappingMethods*)0,   /* tp_as_mapping */
    (hashfunc)0,             /* tp_hash */
    (ternaryfunc)0,          /* tp_call */
    (reprfunc)0,              /* tp_str */
    (getattrofunc)0,     /* tp_getattro */
    (setattrofunc)0,     /* tp_setattro */
    (PyBufferProcs*)0,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)0,     /* tp_traverse */
    (inquiry)0,             /* tp_clear */
    (richcmpfunc)0,   /* tp_richcompare */
    0,             /* tp_weaklistoffset */
    (getiterfunc)0,          /* tp_iter */
    (iternextfunc)0,     /* tp_iternext */
    (struct PyMethodDef*)_PyMooPaneParams_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    (struct PyGetSetDef*)moo_pane_params_getsets,  /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)0,    /* tp_descr_get */
    (descrsetfunc)0,    /* tp_descr_set */
    0,                 /* tp_dictoffset */
    (initproc)_wrap_moo_pane_params_new,             /* tp_init */
    (allocfunc)0,           /* tp_alloc */
    (newfunc)0,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)0              /* tp_is_gc */
};



/* ----------- MooBigPaned ----------- */

static int
_wrap_moo_big_paned_new(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char* kwlist[] = { NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     ":moo_stub.BigPaned.__init__",
                                     kwlist))
        return -1;

    pygobject_constructv(self, 0, NULL);
    if (!self->obj) {
        PyErr_SetString(
            PyExc_RuntimeError, 
            "could not create moo_stub.BigPaned object");
        return -1;
    }
    return 0;
}

#line 4 "moopaned.override"
static PyObject *
_wrap_moo_big_paned_find_pane (PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { (char*) "pane_widget", NULL };
    PyGObject *widget;
    MooPaned *child;
    PyObject *ret;
    MooPane *pane;

    if (!PyArg_ParseTupleAndKeywords (args, kwargs,
                                      (char*) "O!:MooBigPaned.find_pane", kwlist,
                                      &PyGtkWidget_Type, &widget))
        return NULL;

    pane = moo_big_paned_find_pane (MOO_BIG_PANED (self->obj), GTK_WIDGET (widget->obj), &child);

    if (!pane)
    {
        Py_INCREF (Py_None);
        return Py_None;
    }

    ret = PyTuple_New (2);
    PyTuple_SET_ITEM (ret, 0, pygobject_new (G_OBJECT (pane)));
    PyTuple_SET_ITEM (ret, 1, pygobject_new (G_OBJECT (child)));

    return ret;
}
#line 343 "moo-pygtk.c"


static PyObject *
_wrap_moo_big_paned_add_child(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "widget", NULL };
    PyGObject *widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.add_child", kwlist, &PyGtkWidget_Type, &widget))
        return NULL;
    
    moo_big_paned_add_child(MOO_BIG_PANED(self->obj), GTK_WIDGET(widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_remove_child(PyGObject *self)
{
    
    moo_big_paned_remove_child(MOO_BIG_PANED(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_get_child(PyGObject *self)
{
    GtkWidget *ret;

    
    ret = moo_big_paned_get_child(MOO_BIG_PANED(self->obj));
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_big_paned_get_paned(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "position", NULL };
    PyObject *py_position = NULL;
    MooPaned *ret;
    MooPanePosition position;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O:MooBigPaned.get_paned", kwlist, &py_position))
        return NULL;
    if (pyg_enum_get_value(MOO_TYPE_PANE_POSITION, py_position, (gpointer)&position))
        return NULL;
    
    ret = moo_big_paned_get_paned(MOO_BIG_PANED(self->obj), position);
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_big_paned_insert_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", "pane_label", "position", "index_", NULL };
    MooPanePosition position;
    PyObject *py_pane_label, *py_position = NULL;
    int index_;
    PyGObject *pane_widget;
    MooPaneLabel *pane_label = NULL;
    MooPane *ret;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!OOi:MooBigPaned.insert_pane", kwlist, &PyGtkWidget_Type, &pane_widget, &py_pane_label, &py_position, &index_))
        return NULL;
    if (pyg_boxed_check(py_pane_label, MOO_TYPE_PANE_LABEL))
        pane_label = pyg_boxed_get(py_pane_label, MooPaneLabel);
    else {
        PyErr_SetString(PyExc_TypeError, "pane_label should be a MooPaneLabel");
        return NULL;
    }
    if (pyg_enum_get_value(MOO_TYPE_PANE_POSITION, py_position, (gpointer)&position))
        return NULL;
    
    ret = moo_big_paned_insert_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj), pane_label, position, index_);
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_big_paned_remove_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;
    int ret;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.remove_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    ret = moo_big_paned_remove_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_big_paned_get_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "position", "index_", NULL };
    PyObject *py_position = NULL;
    int index_;
    GtkWidget *ret;
    MooPanePosition position;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"Oi:MooBigPaned.get_pane", kwlist, &py_position, &index_))
        return NULL;
    if (pyg_enum_get_value(MOO_TYPE_PANE_POSITION, py_position, (gpointer)&position))
        return NULL;
    
    ret = moo_big_paned_get_pane(MOO_BIG_PANED(self->obj), position, index_);
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_big_paned_open_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.open_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    moo_big_paned_open_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_hide_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.hide_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    moo_big_paned_hide_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_present_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.present_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    moo_big_paned_present_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_attach_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.attach_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    moo_big_paned_attach_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_big_paned_detach_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooBigPaned.detach_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    moo_big_paned_detach_pane(MOO_BIG_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static const PyMethodDef _PyMooBigPaned_methods[] = {
    { "find_pane", (PyCFunction)_wrap_moo_big_paned_find_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "find_pane(pane_widget) -> (pane, paned) or None." },
    { "add_child", (PyCFunction)_wrap_moo_big_paned_add_child, METH_VARARGS|METH_KEYWORDS,
      (char *) "add_child(widget) -> None.\n"
"\n"
"Analogous to gtk.Container.add(), adds widget as the main child of BigPaned widget." },
    { "remove_child", (PyCFunction)_wrap_moo_big_paned_remove_child, METH_NOARGS,
      (char *) "remove_child() -> None.\n"
"\n"
"Analogous to gtk.Container.remove(), removes the main child widget." },
    { "get_child", (PyCFunction)_wrap_moo_big_paned_get_child, METH_NOARGS,
      (char *) "get_child() -> gtk.Widget.\n"
"\n"
"Returns the main child widget." },
    { "get_paned", (PyCFunction)_wrap_moo_big_paned_get_paned, METH_VARARGS|METH_KEYWORDS,
      (char *) "get_paned(pos) -> Paned.\n"
"\n"
"Returns the paned widget at position pos." },
    { "insert_pane", (PyCFunction)_wrap_moo_big_paned_insert_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "insert_pane(pane_widget, pane_label, position, index) -> Pane.\n"
"\n"
"Returns newly created pane object." },
    { "remove_pane", (PyCFunction)_wrap_moo_big_paned_remove_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "remove_pane(pane_widget) -> bool.\n"
"\n"
"Returns True if pane_widget was removed." },
    { "get_pane", (PyCFunction)_wrap_moo_big_paned_get_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "get_pane(position, index) -> gtk.Widget." },
    { "open_pane", (PyCFunction)_wrap_moo_big_paned_open_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "open_pane(pane_widget) -> None." },
    { "hide_pane", (PyCFunction)_wrap_moo_big_paned_hide_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "hide_pane(pane_widget) -> None." },
    { "present_pane", (PyCFunction)_wrap_moo_big_paned_present_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "present_pane(pane_widget) -> None.\n"
"\n"
"Opens the pane or presents the pane window if it's detached." },
    { "attach_pane", (PyCFunction)_wrap_moo_big_paned_attach_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "attach_pane(pane_widget) -> None." },
    { "detach_pane", (PyCFunction)_wrap_moo_big_paned_detach_pane, METH_VARARGS|METH_KEYWORDS,
      (char *) "detach_pane(pane_widget) -> None." },
    { NULL, NULL, 0, NULL }
};

PyTypeObject G_GNUC_INTERNAL PyMooBigPaned_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "moo_stub.BigPaned",                   /* tp_name */
    sizeof(PyGObject),          /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)0,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)0,       /* tp_getattr */
    (setattrfunc)0,       /* tp_setattr */
    (cmpfunc)0,           /* tp_compare */
    (reprfunc)0,             /* tp_repr */
    (PyNumberMethods*)0,     /* tp_as_number */
    (PySequenceMethods*)0, /* tp_as_sequence */
    (PyMappingMethods*)0,   /* tp_as_mapping */
    (hashfunc)0,             /* tp_hash */
    (ternaryfunc)0,          /* tp_call */
    (reprfunc)0,              /* tp_str */
    (getattrofunc)0,     /* tp_getattro */
    (setattrofunc)0,     /* tp_setattro */
    (PyBufferProcs*)0,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)0,     /* tp_traverse */
    (inquiry)0,             /* tp_clear */
    (richcmpfunc)0,   /* tp_richcompare */
    offsetof(PyGObject, weakreflist),             /* tp_weaklistoffset */
    (getiterfunc)0,          /* tp_iter */
    (iternextfunc)0,     /* tp_iternext */
    (struct PyMethodDef*)_PyMooBigPaned_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    (struct PyGetSetDef*)0,  /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)0,    /* tp_descr_get */
    (descrsetfunc)0,    /* tp_descr_set */
    offsetof(PyGObject, inst_dict),                 /* tp_dictoffset */
    (initproc)_wrap_moo_big_paned_new,             /* tp_init */
    (allocfunc)0,           /* tp_alloc */
    (newfunc)0,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)0              /* tp_is_gc */
};



/* ----------- MooPaned ----------- */

static int
_wrap_moo_paned_new(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    GType obj_type = pyg_type_from_object((PyObject *) self);
    GParameter params[1];
    PyObject *parsed_args[1] = {NULL, };
    char *arg_names[] = {"pane_position", NULL };
    char *prop_names[] = {"pane_position", NULL };
    guint nparams, i;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O:moo_stub.Paned.__init__" , arg_names , &parsed_args[0]))
        return -1;

    memset(params, 0, sizeof(GParameter)*1);
    if (!pyg_parse_constructor_args(obj_type, arg_names,
                                    prop_names, params, 
                                    &nparams, parsed_args))
        return -1;
    pygobject_constructv(self, nparams, params);
    for (i = 0; i < nparams; ++i)
        g_value_unset(&params[i].value);
    if (!self->obj) {
        PyErr_SetString(
            PyExc_RuntimeError, 
            "could not create moo_stub.Paned object");
        return -1;
    }
    return 0;
}

static PyObject *
_wrap_moo_paned_insert_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", "pane_label", "position", NULL };
    PyGObject *pane_widget;
    PyObject *py_pane_label;
    int position;
    MooPaneLabel *pane_label = NULL;
    MooPane *ret;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!Oi:MooPaned.insert_pane", kwlist, &PyGtkWidget_Type, &pane_widget, &py_pane_label, &position))
        return NULL;
    if (pyg_boxed_check(py_pane_label, MOO_TYPE_PANE_LABEL))
        pane_label = pyg_boxed_get(py_pane_label, MooPaneLabel);
    else {
        PyErr_SetString(PyExc_TypeError, "pane_label should be a MooPaneLabel");
        return NULL;
    }
    
    ret = moo_paned_insert_pane(MOO_PANED(self->obj), GTK_WIDGET(pane_widget->obj), pane_label, position);
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_paned_remove_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane_widget", NULL };
    PyGObject *pane_widget;
    int ret;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.remove_pane", kwlist, &PyGtkWidget_Type, &pane_widget))
        return NULL;
    
    ret = moo_paned_remove_pane(MOO_PANED(self->obj), GTK_WIDGET(pane_widget->obj));
    
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_paned_n_panes(PyGObject *self)
{
    guint ret;

    
    ret = moo_paned_n_panes(MOO_PANED(self->obj));
    
    return PyLong_FromUnsignedLong(ret);
}

static PyObject *
_wrap_moo_paned_get_nth_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "n", NULL };
    PyObject *py_n = NULL;
    MooPane *ret;
    guint n = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O:MooPaned.get_nth_pane", kwlist, &py_n))
        return NULL;
    if (py_n) {
        if (PyLong_Check(py_n))
            n = PyLong_AsUnsignedLong(py_n);
        else if (PyInt_Check(py_n))
            n = PyInt_AsLong(py_n);
        else
            PyErr_SetString(PyExc_TypeError, "Parameter 'n' must be an int or a long");
        if (PyErr_Occurred())
            return NULL;
    }
    
    ret = moo_paned_get_nth_pane(MOO_PANED(self->obj), n);
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_paned_get_pane_num(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "widget", NULL };
    PyGObject *widget;
    int ret;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.get_pane_num", kwlist, &PyGtkWidget_Type, &widget))
        return NULL;
    
    ret = moo_paned_get_pane_num(MOO_PANED(self->obj), GTK_WIDGET(widget->obj));
    
    return PyInt_FromLong(ret);
}

static PyObject *
_wrap_moo_paned_set_sticky_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "sticky", NULL };
    int sticky;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"i:MooPaned.set_sticky_pane", kwlist, &sticky))
        return NULL;
    
    moo_paned_set_sticky_pane(MOO_PANED(self->obj), sticky);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_set_pane_size(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "size", NULL };
    int size;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"i:MooPaned.set_pane_size", kwlist, &size))
        return NULL;
    
    moo_paned_set_pane_size(MOO_PANED(self->obj), size);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_get_pane_size(PyGObject *self)
{
    int ret;

    
    ret = moo_paned_get_pane_size(MOO_PANED(self->obj));
    
    return PyInt_FromLong(ret);
}

static PyObject *
_wrap_moo_paned_get_button_box_size(PyGObject *self)
{
    int ret;

    
    ret = moo_paned_get_button_box_size(MOO_PANED(self->obj));
    
    return PyInt_FromLong(ret);
}

static PyObject *
_wrap_moo_paned_get_open_pane(PyGObject *self)
{
    MooPane *ret;

    
    ret = moo_paned_get_open_pane(MOO_PANED(self->obj));
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_paned_is_open(PyGObject *self)
{
    int ret;

    
    ret = moo_paned_is_open(MOO_PANED(self->obj));
    
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_paned_open_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane", NULL };
    PyGObject *pane;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.open_pane", kwlist, &PyMooPane_Type, &pane))
        return NULL;
    
    moo_paned_open_pane(MOO_PANED(self->obj), MOO_PANE(pane->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_present_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane", NULL };
    PyGObject *pane;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.present_pane", kwlist, &PyMooPane_Type, &pane))
        return NULL;
    
    moo_paned_present_pane(MOO_PANED(self->obj), MOO_PANE(pane->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_hide_pane(PyGObject *self)
{
    
    moo_paned_hide_pane(MOO_PANED(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_detach_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane", NULL };
    PyGObject *pane;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.detach_pane", kwlist, &PyMooPane_Type, &pane))
        return NULL;
    
    moo_paned_detach_pane(MOO_PANED(self->obj), MOO_PANE(pane->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_paned_attach_pane(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "pane", NULL };
    PyGObject *pane;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O!:MooPaned.attach_pane", kwlist, &PyMooPane_Type, &pane))
        return NULL;
    
    moo_paned_attach_pane(MOO_PANED(self->obj), MOO_PANE(pane->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static const PyMethodDef _PyMooPaned_methods[] = {
    { "insert_pane", (PyCFunction)_wrap_moo_paned_insert_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "remove_pane", (PyCFunction)_wrap_moo_paned_remove_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "n_panes", (PyCFunction)_wrap_moo_paned_n_panes, METH_NOARGS,
      NULL },
    { "get_nth_pane", (PyCFunction)_wrap_moo_paned_get_nth_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_pane_num", (PyCFunction)_wrap_moo_paned_get_pane_num, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "set_sticky_pane", (PyCFunction)_wrap_moo_paned_set_sticky_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "set_pane_size", (PyCFunction)_wrap_moo_paned_set_pane_size, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_pane_size", (PyCFunction)_wrap_moo_paned_get_pane_size, METH_NOARGS,
      NULL },
    { "get_button_box_size", (PyCFunction)_wrap_moo_paned_get_button_box_size, METH_NOARGS,
      NULL },
    { "get_open_pane", (PyCFunction)_wrap_moo_paned_get_open_pane, METH_NOARGS,
      NULL },
    { "is_open", (PyCFunction)_wrap_moo_paned_is_open, METH_NOARGS,
      NULL },
    { "open_pane", (PyCFunction)_wrap_moo_paned_open_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "present_pane", (PyCFunction)_wrap_moo_paned_present_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "hide_pane", (PyCFunction)_wrap_moo_paned_hide_pane, METH_NOARGS,
      NULL },
    { "detach_pane", (PyCFunction)_wrap_moo_paned_detach_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "attach_pane", (PyCFunction)_wrap_moo_paned_attach_pane, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { NULL, NULL, 0, NULL }
};

static PyObject *
_wrap_moo_paned__get_button_box(PyObject *self, void *closure)
{
    GtkWidget *ret;

    ret = MOO_PANED(pygobject_get(self))->button_box;
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static const PyGetSetDef moo_paned_getsets[] = {
    { "button_box", (getter)_wrap_moo_paned__get_button_box, (setter)0 },
    { NULL, (getter)0, (setter)0 },
};

PyTypeObject G_GNUC_INTERNAL PyMooPaned_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "moo_stub.Paned",                   /* tp_name */
    sizeof(PyGObject),          /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)0,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)0,       /* tp_getattr */
    (setattrfunc)0,       /* tp_setattr */
    (cmpfunc)0,           /* tp_compare */
    (reprfunc)0,             /* tp_repr */
    (PyNumberMethods*)0,     /* tp_as_number */
    (PySequenceMethods*)0, /* tp_as_sequence */
    (PyMappingMethods*)0,   /* tp_as_mapping */
    (hashfunc)0,             /* tp_hash */
    (ternaryfunc)0,          /* tp_call */
    (reprfunc)0,              /* tp_str */
    (getattrofunc)0,     /* tp_getattro */
    (setattrofunc)0,     /* tp_setattro */
    (PyBufferProcs*)0,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)0,     /* tp_traverse */
    (inquiry)0,             /* tp_clear */
    (richcmpfunc)0,   /* tp_richcompare */
    offsetof(PyGObject, weakreflist),             /* tp_weaklistoffset */
    (getiterfunc)0,          /* tp_iter */
    (iternextfunc)0,     /* tp_iternext */
    (struct PyMethodDef*)_PyMooPaned_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    (struct PyGetSetDef*)moo_paned_getsets,  /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)0,    /* tp_descr_get */
    (descrsetfunc)0,    /* tp_descr_set */
    offsetof(PyGObject, inst_dict),                 /* tp_dictoffset */
    (initproc)_wrap_moo_paned_new,             /* tp_init */
    (allocfunc)0,           /* tp_alloc */
    (newfunc)0,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)0              /* tp_is_gc */
};



/* ----------- MooPane ----------- */

static PyObject *
_wrap_moo_pane_set_label(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "label", NULL };
    PyObject *py_label;
    MooPaneLabel *label = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O:MooPane.set_label", kwlist, &py_label))
        return NULL;
    if (pyg_boxed_check(py_label, MOO_TYPE_PANE_LABEL))
        label = pyg_boxed_get(py_label, MooPaneLabel);
    else {
        PyErr_SetString(PyExc_TypeError, "label should be a MooPaneLabel");
        return NULL;
    }
    
    moo_pane_set_label(MOO_PANE(self->obj), label);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_get_label(PyGObject *self)
{
    MooPaneLabel *ret;

    
    ret = moo_pane_get_label(MOO_PANE(self->obj));
    
    /* pyg_boxed_new handles NULL checking */
    return pyg_boxed_new(MOO_TYPE_PANE_LABEL, ret, TRUE, TRUE);
}

static PyObject *
_wrap_moo_pane_set_params(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "params", NULL };
    PyObject *py_params;
    MooPaneParams *params = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"O:MooPane.set_params", kwlist, &py_params))
        return NULL;
    if (pyg_boxed_check(py_params, MOO_TYPE_PANE_PARAMS))
        params = pyg_boxed_get(py_params, MooPaneParams);
    else {
        PyErr_SetString(PyExc_TypeError, "params should be a MooPaneParams");
        return NULL;
    }
    
    moo_pane_set_params(MOO_PANE(self->obj), params);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_get_params(PyGObject *self)
{
    MooPaneParams *ret;

    
    ret = moo_pane_get_params(MOO_PANE(self->obj));
    
    /* pyg_boxed_new handles NULL checking */
    return pyg_boxed_new(MOO_TYPE_PANE_PARAMS, ret, TRUE, TRUE);
}

static PyObject *
_wrap_moo_pane_set_detachable(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "detachable", NULL };
    int detachable;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"i:MooPane.set_detachable", kwlist, &detachable))
        return NULL;
    
    moo_pane_set_detachable(MOO_PANE(self->obj), detachable);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_get_detachable(PyGObject *self)
{
    int ret;

    
    ret = moo_pane_get_detachable(MOO_PANE(self->obj));
    
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_pane_set_removable(PyGObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = { "removable", NULL };
    int removable;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,"i:MooPane.set_removable", kwlist, &removable))
        return NULL;
    
    moo_pane_set_removable(MOO_PANE(self->obj), removable);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_get_removable(PyGObject *self)
{
    int ret;

    
    ret = moo_pane_get_removable(MOO_PANE(self->obj));
    
    return PyBool_FromLong(ret);

}

static PyObject *
_wrap_moo_pane_get_child(PyGObject *self)
{
    GtkWidget *ret;

    
    ret = moo_pane_get_child(MOO_PANE(self->obj));
    
    /* pygobject_new handles NULL checking */
    return pygobject_new((GObject *)ret);
}

static PyObject *
_wrap_moo_pane_get_index(PyGObject *self)
{
    int ret;

    
    ret = moo_pane_get_index(MOO_PANE(self->obj));
    
    return PyInt_FromLong(ret);
}

static PyObject *
_wrap_moo_pane_open(PyGObject *self)
{
    
    moo_pane_open(MOO_PANE(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_present(PyGObject *self)
{
    
    moo_pane_present(MOO_PANE(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_attach(PyGObject *self)
{
    
    moo_pane_attach(MOO_PANE(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
_wrap_moo_pane_detach(PyGObject *self)
{
    
    moo_pane_detach(MOO_PANE(self->obj));
    
    Py_INCREF(Py_None);
    return Py_None;
}

static const PyMethodDef _PyMooPane_methods[] = {
    { "set_label", (PyCFunction)_wrap_moo_pane_set_label, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_label", (PyCFunction)_wrap_moo_pane_get_label, METH_NOARGS,
      NULL },
    { "set_params", (PyCFunction)_wrap_moo_pane_set_params, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_params", (PyCFunction)_wrap_moo_pane_get_params, METH_NOARGS,
      NULL },
    { "set_detachable", (PyCFunction)_wrap_moo_pane_set_detachable, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_detachable", (PyCFunction)_wrap_moo_pane_get_detachable, METH_NOARGS,
      NULL },
    { "set_removable", (PyCFunction)_wrap_moo_pane_set_removable, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "get_removable", (PyCFunction)_wrap_moo_pane_get_removable, METH_NOARGS,
      NULL },
    { "get_child", (PyCFunction)_wrap_moo_pane_get_child, METH_NOARGS,
      NULL },
    { "get_index", (PyCFunction)_wrap_moo_pane_get_index, METH_NOARGS,
      NULL },
    { "open", (PyCFunction)_wrap_moo_pane_open, METH_NOARGS,
      NULL },
    { "present", (PyCFunction)_wrap_moo_pane_present, METH_NOARGS,
      NULL },
    { "attach", (PyCFunction)_wrap_moo_pane_attach, METH_NOARGS,
      NULL },
    { "detach", (PyCFunction)_wrap_moo_pane_detach, METH_NOARGS,
      NULL },
    { NULL, NULL, 0, NULL }
};

PyTypeObject G_GNUC_INTERNAL PyMooPane_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "moo_stub.Pane",                   /* tp_name */
    sizeof(PyGObject),          /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)0,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)0,       /* tp_getattr */
    (setattrfunc)0,       /* tp_setattr */
    (cmpfunc)0,           /* tp_compare */
    (reprfunc)0,             /* tp_repr */
    (PyNumberMethods*)0,     /* tp_as_number */
    (PySequenceMethods*)0, /* tp_as_sequence */
    (PyMappingMethods*)0,   /* tp_as_mapping */
    (hashfunc)0,             /* tp_hash */
    (ternaryfunc)0,          /* tp_call */
    (reprfunc)0,              /* tp_str */
    (getattrofunc)0,     /* tp_getattro */
    (setattrofunc)0,     /* tp_setattro */
    (PyBufferProcs*)0,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)0,     /* tp_traverse */
    (inquiry)0,             /* tp_clear */
    (richcmpfunc)0,   /* tp_richcompare */
    offsetof(PyGObject, weakreflist),             /* tp_weaklistoffset */
    (getiterfunc)0,          /* tp_iter */
    (iternextfunc)0,     /* tp_iternext */
    (struct PyMethodDef*)_PyMooPane_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    (struct PyGetSetDef*)0,  /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)0,    /* tp_descr_get */
    (descrsetfunc)0,    /* tp_descr_set */
    offsetof(PyGObject, inst_dict),                 /* tp_dictoffset */
    (initproc)0,             /* tp_init */
    (allocfunc)0,           /* tp_alloc */
    (newfunc)0,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)0              /* tp_is_gc */
};



/* ----------- functions ----------- */

const PyMethodDef _moo_stub_functions[] = {
    { NULL, NULL, 0, NULL }
};


/* ----------- enums and flags ----------- */

void
_moo_stub_add_constants(PyObject *module, const gchar *strip_prefix)
{
#ifdef VERSION
    PyModule_AddStringConstant(module, "__version__", VERSION);
#endif
  pyg_enum_add(module, "PanePosition", strip_prefix, MOO_TYPE_PANE_POSITION);

  if (PyErr_Occurred())
    PyErr_Print();
}

/* initialise stuff extension classes */
void
_moo_stub_register_classes(PyObject *d)
{
    PyObject *module;

    if ((module = PyImport_ImportModule("gtk")) != NULL) {
        _PyGtkObject_Type = (PyTypeObject *)PyObject_GetAttrString(module, "Object");
        if (_PyGtkObject_Type == NULL) {
            PyErr_SetString(PyExc_ImportError,
                "cannot import name Object from gtk");
            return ;
        }
        _PyGtkWidget_Type = (PyTypeObject *)PyObject_GetAttrString(module, "Widget");
        if (_PyGtkWidget_Type == NULL) {
            PyErr_SetString(PyExc_ImportError,
                "cannot import name Widget from gtk");
            return ;
        }
        _PyGtkFrame_Type = (PyTypeObject *)PyObject_GetAttrString(module, "Frame");
        if (_PyGtkFrame_Type == NULL) {
            PyErr_SetString(PyExc_ImportError,
                "cannot import name Frame from gtk");
            return ;
        }
        _PyGtkBin_Type = (PyTypeObject *)PyObject_GetAttrString(module, "Bin");
        if (_PyGtkBin_Type == NULL) {
            PyErr_SetString(PyExc_ImportError,
                "cannot import name Bin from gtk");
            return ;
        }
    } else {
        PyErr_SetString(PyExc_ImportError,
            "could not import gtk");
        return ;
    }
    if ((module = PyImport_ImportModule("gtk.gdk")) != NULL) {
        _PyGdkPixbuf_Type = (PyTypeObject *)PyObject_GetAttrString(module, "Pixbuf");
        if (_PyGdkPixbuf_Type == NULL) {
            PyErr_SetString(PyExc_ImportError,
                "cannot import name Pixbuf from gtk.gdk");
            return ;
        }
    } else {
        PyErr_SetString(PyExc_ImportError,
            "could not import gtk.gdk");
        return ;
    }


#line 1339 "moo-pygtk.c"
    pyg_register_boxed(d, "PaneLabel", MOO_TYPE_PANE_LABEL, &PyMooPaneLabel_Type);
    pyg_register_boxed(d, "PaneParams", MOO_TYPE_PANE_PARAMS, &PyMooPaneParams_Type);
    pygobject_register_class(d, "MooBigPaned", MOO_TYPE_BIG_PANED, &PyMooBigPaned_Type, Py_BuildValue("(O)", &PyGtkFrame_Type));
    pyg_set_object_has_new_constructor(MOO_TYPE_BIG_PANED);
    pygobject_register_class(d, "MooPaned", MOO_TYPE_PANED, &PyMooPaned_Type, Py_BuildValue("(O)", &PyGtkBin_Type));
    pyg_set_object_has_new_constructor(MOO_TYPE_PANED);
    pygobject_register_class(d, "MooPane", MOO_TYPE_PANE, &PyMooPane_Type, Py_BuildValue("(O)", &PyGtkObject_Type));
}
