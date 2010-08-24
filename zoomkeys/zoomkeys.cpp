#include <Python.h>
#include <QtGui>
#include <QtGui/QX11Info>
#include <X11/Xlib.h>
#include <X11/Xatom.h>

/*
Needed to install : libqt4-dev python-dev python2.5-qt4-dev
Compile & Install : python setup.py install
Usage : 

import zoomkeys
# grap buttons
zoomkeys.grab(mywindow.winId(), True)
# release them
zoomkeys.grab(mywindow.winId(), False)
*/

static PyObject *
zoomkeys_grab(PyObject *self, PyObject *args);

static PyMethodDef ZoomKeyMethods[] = {
    {   "grab", 
        zoomkeys_grab, 
        METH_VARARGS,
        "Grab zoom keys."
    },
    {NULL, NULL, 0, NULL} /* Sentinel */
};

PyMODINIT_FUNC
initzoomkeys(void) {
    (void) Py_InitModule("zoomkeys", ZoomKeyMethods);
}

static PyObject *
zoomkeys_grab(PyObject *self, PyObject *args) {
    int winId;
    int grab;
    
    if (!PyArg_ParseTuple(args, "ii", &winId, &grab))
        return NULL;

    if (!winId) {
        qWarning("Can't grab keys unless we have a window id");
        return NULL;
    }

    unsigned long val = (grab) ? 1 : 0;
    Atom atom = XInternAtom(QX11Info::display(), "_HILDON_ZOOM_KEY_ATOM", False);
    if (!atom) {
         qWarning("Unable to obtain _HILDON_ZOOM_KEY_ATOM. This example will only work "
                  "on a Maemo 5 device!");
        return NULL;
    }

    XChangeProperty (QX11Info::display(),
        winId,
        atom,
        XA_INTEGER,
        32,
        PropModeReplace,
        reinterpret_cast<unsigned char *>(&val),
        1
    );

    return Py_None;
}
