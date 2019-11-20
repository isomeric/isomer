Q: I have a too old version of python3-six installed!
A: Remove it: apt-get remove python3-six

Q: The pynacl bindings could not be compiled! Errors like:

c/_cffi_backend.c:2:20: fatal error: Python.h: No such file or directory
 #include <Python.h>

or

unable to execute 'x86_64-linux-gnu-gcc': No such file or directory

A: Try the following:

a) apt-get install python3-cryptography

or if that doesn't resolve the situation, let it build manually:

b) apt-get install build-essential python3-dev libffi-dev
