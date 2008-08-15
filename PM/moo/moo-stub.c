#include <Python.h>
#include <pygobject.h>
#include <pygtk/pygtk.h>

extern PyMethodDef _moo_stub_functions[];
void _moo_stub_add_constants(PyObject *module, const gchar *strip_prefix);
void _moo_stub_register_classes(PyObject *d);

void
initmoo_stub (void)
{
    PyObject *module;

    init_pygobject ();
    init_pygtk ();

    if (PyErr_Occurred ())
        return;

    module = Py_InitModule ((char*) "moo_stub", _moo_stub_functions);

    if (module)
    {
        _moo_stub_add_constants (module, "MOO_");
        _moo_stub_register_classes (PyModule_GetDict (module));
    }
}
