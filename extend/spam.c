#include<python3.5/Python.h>
#include<stdio.h>


static PyObject *spam_system(PyObject *self,PyObject *args){
	const char *cmd;
	int sts;
	if(!PyArg_ParseTuple(args,"s",&cmd))
		return NULL;
	sts = system(cmd);
	return PyLong_FromLong(sts);
	//return Py_BuildValue("i",sts);
}

static PyMethodDef SpamMethods[]={
{"system",spam_system,METH_VARARGS,"Execute a shell command."},
{NULL,NULL,0,NULL}
};

static struct PyModuleDef module_spam={
PyModuleDef_HEAD_INIT,
"spam",
"PY C",
-1,
SpamMethods
};

PyMODINIT_FUNC PyInit_spam(void){
	return PyModule_Create(&module_spam);
}
