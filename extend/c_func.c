#include<python3.5m/Python.h>

static PyObject *c_func(PyObject *self,PyObject *args)
{
	const char *str;
	if(!PyArg_ParseTuple(args,"s",&str)) return NULL;
	printf("%s\n",str);
	Py_RETURN_NONE;
}

static PyMethodDef methods[]={
	{"c_func",c_func,METH_VARARGS,"print a string"},
	{0,0,0,0}
};

static struct PyModuleDef module={
PyModuleDef_HEAD_INIT,
"c_func",
"test module",
-1,
methods
};

PyMODINIT_FUNC PyInit_c_func(){
	PyObject *M;
	M = PyModule_Create(&module);
	if(M == NULL) return NULL;
	return M;
};
