#include <stddef.h>
#include <Python.h>
#include "db.h"
#include "bsddb.h"


// To compile on OS X:
// export BERKELEYDBPATH=/usr/local/BerkeleyDB.5.3
// export BSDDB3PATH=$HOME/src/bsddb3-5.3.0/Modules
// rm emen2/db/bulk.*o
// gcc -fno-strict-aliasing -fno-common -dynamic -g -fwrapv -Os -Wall -Wstrict-prototypes  -pipe -I${BERKELEYDBPATH}/include -I/System/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -I${BSDDB3PATH} -c emen2/db/bulk.c -o emen2/db/bulk.o
// gcc -Wl,-F. -bundle -undefined dynamic_lookup -L${BERKELEYDBPATH}/lib -ldb emen2/db/bulk.o -o emen2/db/bulk.so 
// python -c "import emen2.db.bulk"


// Linux -- new
// gcc -pthread -fno-strict-aliasing -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes -fPIC -DPYBSDDB_STANDALONE=1 -I/usr/local/BerkeleyDB.5.3/include -I/home/emen2/EMAN2/Python/include/python2.7  -I/home/emen2/bsddb3-5.3.0/Modules/  -c test/emen2/emen2/db/bulk.c -o bulk.o
// gcc -pthread -shared db/bulk.o -L/usr/local/BerkeleyDB.4.8/lib -Wl,-R/usr/local/BerkeleyDB.4.8/lib -ldb-4.8 -o db/bulk.so




/*
err = cursor->dbc->get(cursor->dbc, &key, &data, DB_FIRST);
while (err != DB_NOTFOUND) {
    err = cursor->dbc->get(cursor->dbc, &key, &data, DB_NEXT_DUP);
    item = PyString_FromStringAndSize((char *)data.data, data.size);

    if (item != NULL) {
        PyList_Append(set, item);
        Py_DECREF(item);
    }

}
*/


// static PyObject*
// testwtf(PyObject *self, PyObject *args, PyObject *kwargs) {
//       PyObject* set;
//    PyObject* keyobj;
//    static char *kwlist[] = {"key", NULL};
// 
//    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", kwlist, &keyobj)) {return NULL;}
// 
//    set = PyList_New(NULL);
//    return set;
// }


// static PyObject*
// DBC_get_dup_items(PyObject *self, PyObject *args, PyObject *kwargs) {
//    
// }




static PyObject*
notbulk(DBCursorObject *cursor, PyObject *keyobj, char dtype) { 

    /* common */
    DBT key, data;
    int err;
    char *retcopy = malloc(128);
    PyObject* list;
    PyObject* item = NULL;
    PyObject* set;

    list = PyList_New((Py_ssize_t)NULL);
    if (list == NULL)
        return NULL;
    
    // initalize the DBTs
    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    key.data = PyString_AS_STRING(keyobj);
    key.size = PyString_GET_SIZE(keyobj);
    /* end common */
    

    Py_BEGIN_ALLOW_THREADS
    err = cursor->dbc->c_get(cursor->dbc, &key, &data, DB_SET);
    Py_END_ALLOW_THREADS

    while (err == 0) { // != DB_NOTFOUND
        
        //printf("key: %s, data: %s\n", (char *)key.data, (char *)data.data);

        if (dtype == 'd') {
            memcpy(retcopy, data.data, data.size);
            retcopy[data.size] = '\0';
            item = PyInt_FromString(retcopy, 0, 10);
        } else if ( dtype == 's' ) {
            item = PyUnicode_DecodeUTF8((char *)data.data, data.size, NULL);
        } else {
            item = PyString_FromStringAndSize((char *)data.data, data.size);
        }    
            
        if (item != NULL) {
            PyList_Append(list, item);
            Py_DECREF(item);
        }

        Py_BEGIN_ALLOW_THREADS
        err = cursor->dbc->c_get(cursor->dbc, &key, &data, DB_NEXT_DUP);
        Py_END_ALLOW_THREADS

    }
    
    free(retcopy);
    
    set = PySet_New(list);
    if (set == NULL)
        return NULL;

    Py_DECREF(list);    
    
    return (set);
}



static PyObject*
bulk(DBCursorObject *cursor, PyObject *keyobj, char dtype) {    

    /* common */
    size_t retdlen;
    int err;
    void *p;    
    char *retdata;
    char *retcopy = malloc(128);

    DBT key, data, data2;

    PyObject* list;
    PyObject* item = NULL;
    PyObject* set;

    list = PyList_New((Py_ssize_t)NULL);
    if (list == NULL)
        return NULL;


    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));
    memset(&data2, 0, sizeof(data2));

    key.data = PyString_AS_STRING(keyobj);
    key.size = PyString_GET_SIZE(keyobj);
    /* end common */
    

    
    // review in 4 MB chunks
    unsigned long blen = 4*1024*1024;
    if ((data2.data = malloc(blen)) == NULL) {return NULL;}
    data2.ulen = blen;
    data2.flags = DB_DBT_USERMEM;


    // get the first item, add it to the list..
    Py_BEGIN_ALLOW_THREADS
    err = cursor->dbc->c_get(cursor->dbc, &key, &data, DB_SET);
    Py_END_ALLOW_THREADS
    
    if (err == 0) {
        // ian: todo: put this in a function because it's used in 3 places
        if (dtype == 'd') {
            memcpy(retcopy, data.data, data.size);
            retcopy[data.size] = '\0';
            item = PyInt_FromString(retcopy, 0, 10);
        } else if ( dtype == 's' ) {
            item = PyUnicode_DecodeUTF8((char *)data.data, data.size, NULL);
        } else {
            item = PyString_FromStringAndSize((char *)data.data, data.size);
        }    
        
        if (item != NULL) {
            PyList_Append(list, item);
            Py_DECREF(item);
        }
    }
    

    for (;;) {
        
        Py_BEGIN_ALLOW_THREADS
        err = cursor->dbc->c_get(cursor->dbc, &key, &data2, DB_NEXT_DUP | DB_MULTIPLE);
        Py_END_ALLOW_THREADS
                
        if (err != 0) {
            break;
        }

        for (DB_MULTIPLE_INIT(p, &data2);;) {
            DB_MULTIPLE_NEXT(p, &data2, retdata, retdlen);

            if (p == NULL) {
                break;
            }
            
            //printf("len: %d, data: %.*s, retcopy: %s\n", (int)retdlen, (int)retdlen, retdata, retcopy);
            
            if (dtype == 'd') {
                memcpy(retcopy, retdata, retdlen);
                retcopy[retdlen]='\0';
                item = PyInt_FromString(retcopy, 0, 10);
            } else if ( dtype == 's' ) {
                item = PyUnicode_DecodeUTF8(retdata, retdlen, NULL);
            } else {
                item = PyString_FromStringAndSize(retdata, retdlen);
            }    
            
            if (item != NULL) {
                PyList_Append(list, item);
                Py_DECREF(item);
            }

        }

    }
    
    free(data2.data);
    free(retcopy);
    
    
    set = PySet_New(list);
    if (set == NULL)
        return NULL;

    Py_DECREF(list);
    
    return (set);
}






static PyObject*
DBC_get_dup_bulk(PyObject *self, PyObject *args, PyObject *kwargs) {

    DBCursorObject* cursor;
    PyObject* keyobj;
    char dtype = 's';
    
    static char *kwlist[] = {"cursor", "key", "dtype", NULL};

    // get cursor object and key from python args
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OOc", kwlist, &cursor, &keyobj, &dtype))
        return NULL;

    return bulk(cursor, keyobj, dtype);
    
}


static PyObject*
DBC_get_dup_notbulk(PyObject *self, PyObject *args, PyObject *kwargs) {

    DBCursorObject* cursor;
    PyObject* keyobj;
    char dtype = 's';
    
    static char *kwlist[] = {"cursor", "key", "dtype", NULL};

    // get cursor object and key from python args
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OOc", kwlist, &cursor, &keyobj, &dtype))
        return NULL;

    return notbulk(cursor, keyobj, dtype);
    
}



static PyMethodDef BulkMethods[] = {
    {"get_dup_bulk",  (PyCFunction)DBC_get_dup_bulk, METH_VARARGS | METH_KEYWORDS, "DB Bulk (using bulk interface)"},
    {"get_dup_notbulk",     (PyCFunction)DBC_get_dup_notbulk, METH_VARARGS | METH_KEYWORDS, "DB Get Duplicates (not bulk interface)"},
    {NULL, NULL, 0, NULL}
};



PyMODINIT_FUNC
initbulk(void)
{
     (void) Py_InitModule("bulk", BulkMethods);
}
