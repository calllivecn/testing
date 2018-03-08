#include<python3.5m/Python.h>

static PyObject *py_add(PyObject *self,PyObject *args)
{
	int x,y;
	if(!PyArg_ParseTuple(args,"ii",&x,&y)) return NULL;
	return Py_BuildValue("i",x+y);
}

static PyMethodDef Example[]={
{"py_add",py_add,METH_VARARGS,"return x+y"},
{NULL,NULL,0,NULL}
};

static struct PyModuleDef module_structure={
PyModuleDef_HEAD_INIT,
"example",
"a sample example",
-1,
Example
};

// 模块初始化函数
PyMODINIT_FUNC PyInit_example()
{
	return PyModule_Create(&module_structure);
}

