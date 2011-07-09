import re


SEM_TAKE = intern("take")
SEM_GIVE = intern("give")
SEM_KEEP = intern("keep")

ISL_SEM_TO_SEM = {
    "__isl_take": SEM_TAKE,
    "__isl_give": SEM_GIVE,
    "__isl_keep": SEM_KEEP,
    }

class Argument:
    def __init__(self, name, semantics, ctype):
        self.name = name
        self.semantics = semantics
        self.ctype = ctype

class Method:
    def __init__(self, cls, name, return_semantics, return_type, args):
        self.cls = cls
        self.name = name
        self.return_semantics = return_semantics
        self.return_type = return_type
        self.args = args

    def __repr__(self):
        return "<method %s_%s>" % (self.cls, self.name)




CLASSES = [ "set", "printer", "basic_set", "mat", "vec",
        "map", "basic_map", "local_space", 
        "union_map", "union_set",
        "vertex", "cell", "vertices", "dim_set", "dim",
        "qpolynomial_fold",
        "qpolynomial", "pw_qpolynomial",
        "union_pw_qpolynomial", "term", 
        ]

ENUMS = ["isl_dim_type", "isl_fold"]

SAFE_TYPES = ENUMS + ["int", "unsigned", "uint32_t", "size_t"]
SAFE_IN_TYPES = SAFE_TYPES + ["const char *", "char *"]

DECL_RE = re.compile(r"""
    ((?:\w+\s+)* \*?) (?# return type)
    (\w+) (?# func name)
    \(
    (.*) (?# args)
    \)
    """, 
    re.VERBOSE)
STRUCT_DECL_RE = re.compile(r"struct\s+([a-z_A-Z0-9]+)\s*;")
ARG_RE = re.compile(r"^((?:\w+)\s+)+(\*?)\s*(\w+)$")

def filter_semantics(words):
    semantics = []
    other_words = []
    for w in words:
        if w in ISL_SEM_TO_SEM:
            semantics.append(ISL_SEM_TO_SEM[w])
        else:
            other_words.append(w)

    if semantics:
        assert len(semantics) == 1
        return semantics[0], other_words
    else:
        return None, other_words




class BadArg(ValueError):
    pass

class OddSignature(ValueError):
    pass



def parse_arg(arg):
    if "**" in arg:
        raise BadArg

    if "(*" in arg:
        raise BadArg

    words = arg.split()
    semantics, words = filter_semantics(words)

    words = [w for w in words if w not in ["struct", "enum"]]

    arg_match = ARG_RE.match(" ".join(words))
    assert arg_match is not None, " ".join(words)
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            ctype=(arg_match.group(1)+arg_match.group(2)).strip())






class FunctionData:
    def __init__(self):
        self.classes_to_methods = {}

    def read_header(self, fname):
        inf = open(fname, "rt")
        try:
            lines = inf.readlines()
        finally:
            inf.close()

        i = 0

        current_decl = ""
        while i < len(lines):
            l = lines[i].strip()

            if (not l 
                    or l.startswith("#") 
                    or l.startswith("extern")
                    or STRUCT_DECL_RE.search(l)
                    or l.startswith("typedef")
                    or l == "}"):
                i += 1
            elif "/*" in l:
                while True:
                    if "*/" in l:
                        i += 1
                        break

                    i += 1

                    l = lines[i].strip()
            elif l.endswith("{") :
                while True:
                    if "}" in l:
                        i += 1
                        break

                    i += 1

                    l = lines[i].strip()

            elif not l:
                i += 1

            else:
                decl = ""
                while True:
                    decl = decl + l
                    i += 1
                    open_par_count = sum(1 for i in decl if i == "(")
                    close_par_count = sum(1 for i in decl if i == ")")
                    if open_par_count == close_par_count:
                        break
                    l = lines[i].strip()

                self.parse_decl(decl)

    def parse_decl(self, decl):
        decl_match = DECL_RE.match(decl)
        assert decl_match is not None, decl

        return_type = decl_match.group(1)
        name = decl_match.group(2)
        args = [i.strip() for i in decl_match.group(3).split(",")]

        assert name.startswith("isl_")
        name = name[4:]

        found_class = False
        for cls in CLASSES:
            if name.startswith(cls):
                found_class = True
                break

        assert found_class, name
        name = name[len(cls)+1:]

        if name in ["get_ctx", "free", "cow"]:
            return

        try:
            args = [parse_arg(arg) for arg in args]
        except BadArg:
            print "SKIP:", cls, name
            return

        words = return_type.split()
        return_semantics, words = filter_semantics(words)
        words = [w for w in words if w not in ["struct", "enum"]]
        return_type = " ".join(words)

        cls_meth_list = self.classes_to_methods.setdefault(cls, [])
        cls_meth_list.append(Method(
                cls, name, return_semantics, return_type, args))




def write_exposer(outf, meth):
    extra_stuff = ""
    if meth.return_type.endswith("*") and not meth.return_type.endswith("char *"):
        extra_stuff = ", py::return_value_policy<py::manage_new_object>()"

    py_name = meth.name
    if meth.name == "size":
        py_name = "__len__"
    elif meth.name == "alloc":
        py_name = "__init__"

    outf.write("wrap_%s.def(\"%s\", isl::%s_%s%s);\n" % (
        meth.cls, py_name, meth.cls, meth.name, extra_stuff))




def write_wrapper(outf, meth):
    body = []
    checks = []


    passed_args = []
    input_args = []
    for arg in meth.args:
        if arg.ctype in SAFE_IN_TYPES:
            passed_args.append(arg.name)
            input_args.append("%s %s" % (arg.ctype, arg.name))

        elif arg.ctype == "char *" or arg.ctype == "const char *":
            if arg.semantics is SEM_KEEP:
                passed_args.append("strdup(%s)" % arg.name)
            else:
                passed_args.append(arg.name)
            input_args.append("%s %s" % (arg.ctype, arg.name))

        elif arg.ctype.startswith("isl_int"):
            input_args.append("py::object %s" % ("arg_"+arg.name))
            checks.append("""
                if (!Pympz_Check(arg_%(name)s.ptr()))
                  PYTHON_ERROR(TypeError, "passed invalid arg to isl_%(meth)s for %(name)s");
                """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))
            passed_args.append("reinterpret_cast<PympzObject *>(arg_%s.ptr())->z" % arg.name)

        elif arg.ctype.startswith("isl_"):
            assert arg.ctype.endswith("*"), meth
            arg_cls = arg.ctype[4:-1]

            checks.append("""
                if (!arg_%(name)s || !arg_%(name)s->m_valid)
                  PYTHON_ERROR(ValueError, "passed invalid arg to isl_%(meth)s for %(name)s");
                """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))

            if arg.semantics is SEM_TAKE:
                body.append("arg_%s->m_valid = false;" % arg.name)
            passed_args.append("arg_%s->m_data" % arg.name)
            input_args.append("%s *%s" % (arg_cls, "arg_"+arg.name))

        elif arg.ctype == "FILE *":
            passed_args.append("PyFile_AsFile(arg_%s.ptr())" % arg.name)
            input_args.append("py::object %s" % ("arg_"+arg.name))

        elif arg.ctype == "int *":
            raise OddSignature("int * in "+str(meth))

        else:
            raise NotImplementedError("arg type %s" % arg.ctype)

    processed_return_type = meth.return_type

    if meth.return_type == "void":
        result_capture = ""
    else:
        result_capture = "%s result = " % meth.return_type

    body = checks + body

    body.append("%sisl_%s_%s(%s);" % (
        result_capture, meth.cls, meth.name, ", ".join(passed_args)))

    if meth.return_type in SAFE_TYPES:
        body.append("return result;")

    elif meth.return_type.startswith("isl_"):
        assert meth.return_type.endswith("*"), meth
        ret_cls = meth.return_type[4:-1].strip()

        if not meth.return_semantics is SEM_GIVE:
            raise OddSignature(meth)

        body.append("""
            if (result)
            {
              try
              { return new %(ret_cls)s(result); }
              catch (...)
              {
                isl_%(ret_cls)s_free(result);
                throw;
              }
            }
            else
              PYTHON_ERROR(RuntimeError, "call to isl_%(cls)s_%(name)s failed");
            """ % { 
                "ret_cls": ret_cls,
                "cls": meth.cls,
                "name": meth.name,
                })
        processed_return_type = "%s *" % ret_cls

    elif meth.return_type in ["const char *", "char *"]:
        processed_return_type = "std::string"
        body.append("std::string str_result(result);")
        if meth.return_semantics is SEM_GIVE:
            body.append("free(result);")
        body.append("return str_result;")

    elif meth.return_type == "void":
        pass

    elif meth.return_type == "void *":
        raise OddSignature(meth)

    else:
        raise NotImplementedError, "ret type: %s in %s" % (meth.return_type, meth)

    outf.write("""
        %s %s_%s(%s)
        {
          %s
        }
        """ % (
            processed_return_type, meth.cls, meth.name, 
            ", ".join(input_args),
            "\n".join(body)))




def write_wrappers(expf, wrapf, methods):
    for meth in methods:
        try:
            write_wrapper(wrapf, meth)
            write_exposer(expf, meth)
        except OddSignature:
            print "SKIP (odd sig):", meth

        print "WRAPPED:", meth




def gen_wrapper():
    fdata = FunctionData()
    from os.path import expanduser
    fdata.read_header(expanduser("~/pool/include/isl/dim.h"))
    fdata.read_header(expanduser("~/pool/include/isl/set.h"))
    fdata.read_header(expanduser("~/pool/include/isl/map.h"))
    fdata.read_header(expanduser("~/pool/include/isl/vec.h"))
    fdata.read_header(expanduser("~/pool/include/isl/mat.h"))
    fdata.read_header(expanduser("~/pool/include/isl/local_space.h"))
    fdata.read_header(expanduser("~/pool/include/isl/polynomial.h"))
    fdata.read_header(expanduser("~/pool/include/isl/union_map.h"))
    fdata.read_header(expanduser("~/pool/include/isl/union_set.h"))
    fdata.read_header(expanduser("~/pool/include/isl/printer.h"))
    fdata.read_header(expanduser("~/pool/include/isl/vertices.h"))
    #fdata.read_header(expanduser("~/pool/include/isl/constraint.h"))

    expf = open("src/wrapper/gen-expose.inc", "wt")
    wrapf = open("src/wrapper/gen-wrap.inc", "wt")

    for cls in CLASSES:
        write_wrappers(expf, wrapf, fdata.classes_to_methods[cls])

    expf.close()
    wrapf.close()





if __name__ == "__main__":
    gen_wrapper()
