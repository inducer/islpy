from cffi import FFI

ffi = FFI()
ffi.set_source("_isl_cffi", None)

with open("wrapped-functions.h", "rt") as header_f:
    header = header_f.read()

ffi.cdef(header)

if __name__ == "__main__":
    ffi.compile()
