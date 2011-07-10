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

    @property
    def is_constructor(self):
        return not (self.args and self.args[0].ctype.startswith("isl_"+self.cls))

    def __repr__(self):
        return "<method %s_%s>" % (self.cls, self.name)




CLASSES = [
        "printer",  "mat", "vec",
        "aff", "pw_aff",
        "dim", "constraint",
        "local_space",
        "basic_set", "basic_map",
        "set", "map",
        "basic_set_list", "set_list", "aff_list", "band_list",
        "union_map", "union_set",
        "vertex", "cell", "vertices", "dim_set",

        "qpolynomial_fold", "pw_qpolynomial_fold",
        "union_pw_qpolynomial_fold",
        "union_pw_qpolynomial", "term",
        "qpolynomial", "pw_qpolynomial",

        # fake:
        "equality", "inequality",
        ]

CLASS_MAP = {
        "equality": "constraint",
        "inequality": "constraint",
        }

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

class Undocumented(ValueError):
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

    rebuilt_arg = " ".join(words)
    arg_match = ARG_RE.match(rebuilt_arg)

    assert arg_match is not None, rebuilt_arg
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            ctype=(arg_match.group(1)+arg_match.group(2)).strip())






class FunctionData:
    def __init__(self, include_dirs):
        self.classes_to_methods = {}
        self.include_dirs = include_dirs

    def read_header(self, fname):
        from os.path import join
        success = False
        for inc_dir in self.include_dirs:
            try:
                inf = open(join(inc_dir, fname), "rt")
            except IOError:
                pass
            else:
                success = True
                break

        if not success:
            raise RuntimeError("header '%s' not found" % fname)

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




def write_exposer(outf, meth, arg_names):
    func_name = "isl::%s_%s" % (meth.cls, meth.name)
    py_name = meth.name

    if not meth.is_constructor:
        arg_names[0] = "self"

    args_str = (", py::args(%s)"
            % ", ".join('"%s"' % arg_name for arg_name in arg_names))

    if meth.name == "size":
        py_name = "__len__"

    if meth.is_constructor:
        if meth.name == "alloc":
            py_name = "__init__"

        func_name = "py::make_constructor(%s, py::default_call_policies()%s)" % (func_name, args_str)
        args_str = ""

    extra_stuff = args_str

    outf.write("wrap_%s.def(\"%s\", %s%s);\n" % (
        CLASS_MAP.get(meth.cls, meth.cls), py_name, func_name, extra_stuff))




def write_wrapper(outf, meth):
    body = []
    checks = []


    passed_args = []
    input_args = []
    post_call = []
    extra_ret_vals = []

    #if meth.cls == "aff" and meth.name == "copy":
        #from pudb import set_trace; set_trace()

    arg_names = []

    for arg in meth.args:
        arg_names.append(arg.name)

        if arg.ctype in SAFE_IN_TYPES:
            passed_args.append("arg_"+arg.name)
            input_args.append("%s arg_%s" % (arg.ctype, arg.name))

        elif arg.ctype == "char *" or arg.ctype == "const char *":
            if arg.semantics is SEM_KEEP:
                passed_args.append("strdup(%s)" % arg.name)
            else:
                passed_args.append(arg.name)
            input_args.append("%s %s" % (arg.ctype, arg.name))

        elif arg.ctype == "int *":
            if arg.name == "exact":
                body.append("int arg_%s;" % arg.name)
                passed_args.append("&arg_%s" % arg.name)
                extra_ret_vals.append("arg_%s" % arg.name)
                arg_names.pop()
            else:
                raise OddSignature("int *")

        elif arg.ctype == "isl_int *":
            # assume it's meant as a return value
            body.append("""
                py::object arg_%s(py::handle<>((PyObject *) Pympz_new()));
                """ % arg.name)
            passed_args.append("&(Pympz_AS_MPZ(arg_%s.ptr()))" % arg.name)
            extra_ret_vals.append("arg_%s" % arg.name)

            arg_names.pop()

        elif arg.ctype == "isl_int":
            input_args.append("py::object %s" % ("arg_"+arg.name))
            checks.append("""
                if (!Pympz_Check(arg_%(name)s.ptr()))
                  PYTHON_ERROR(TypeError, "passed invalid arg to isl_%(meth)s for %(name)s");
                """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))
            passed_args.append("Pympz_AS_MPZ(arg_%s.ptr())" % arg.name)

        elif arg.ctype.startswith("isl_"):
            assert arg.ctype.endswith("*"), meth
            arg_cls = arg.ctype[4:-1]

            if arg.semantics is None and arg.ctype != "isl_ctx *":
                raise Undocumented(meth)

            checks.append("""
                if (!arg_%(name)s || !arg_%(name)s->is_valid())
                  PYTHON_ERROR(ValueError, "passed invalid arg to isl_%(meth)s for %(name)s");
                """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))

            if arg.semantics is SEM_TAKE:
                post_call.append("arg_%s->invalidate();" % arg.name)
            passed_args.append("arg_%s->m_data" % arg.name)
            input_args.append("%s *%s" % (arg_cls, "arg_"+arg.name))

        elif arg.ctype == "FILE *":
            passed_args.append("PyFile_AsFile(arg_%s.ptr())" % arg.name)
            input_args.append("py::object %s" % ("arg_"+arg.name))

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

    body += post_call

    if meth.return_type == "int":
        body.append("""
            if (result == -1)
            {
              PYTHON_ERROR(RuntimeError, "call to isl_%(cls)s_%(name)s failed");
            }""" % { "cls": meth.cls, "name": meth.name })

        if meth.name.startswith("is_") or meth.name.startswith("has_"):
            processed_return_type = "bool"

        if extra_ret_vals:
            processed_return_type = "py::object"
            body.append("return py::make_tuple(result, %s);" % ", ".join(extra_ret_vals))
        else:
            body.append("return result;")

    elif meth.return_type in SAFE_TYPES:
        if extra_ret_vals:
            raise NotImplementedError("extra ret val with safe type")

        body.append("return result;")

    elif meth.return_type.startswith("isl_"):

        assert meth.return_type.endswith("*"), meth
        ret_cls = meth.return_type[4:-1].strip()

        if meth.is_constructor:
            processed_return_type = "%s *" % ret_cls
            isl_obj_ret_val = "new %s(result)" % ret_cls
        else:
            processed_return_type = "py::object"
            isl_obj_ret_val = "py::object(handle_from_new_ptr(new %s(result)))" % ret_cls

        if extra_ret_vals:
            isl_obj_ret_val = "py::make_tuple(%s, %s)" % (
                    isl_obj_ret_val, ", ".join(extra_ret_vals))
            if meth.is_constructor:
                raise NotImplementedError("extra ret val on constructor")


        if meth.return_semantics is None:
            raise Undocumented(meth)

        if meth.return_semantics is not SEM_GIVE:
            raise OddSignature("non-give return")

        body.append("""
            if (result)
            {
              try
              { return %(ret_val)s; }
              catch (...)
              {
                isl_%(ret_cls)s_free(result);
                throw;
              }
            }
            else
            {
              PYTHON_ERROR(RuntimeError, "call to isl_%(cls)s_%(name)s failed");
            }
            """ % {
                "ret_cls": ret_cls,
                "ret_val": isl_obj_ret_val,
                "cls": meth.cls,
                "name": meth.name,
                })

    elif meth.return_type in ["const char *", "char *"]:
        if extra_ret_vals:
            raise NotImplementedError("extra ret val with string")

        processed_return_type = "std::string"
        body.append("std::string str_result(result);")
        if meth.return_semantics is SEM_GIVE:
            body.append("free(result);")
        body.append("return str_result;")

    elif meth.return_type == "void":
        if extra_ret_vals:
            processed_return_type = "py::object"
            if len(extra_ret_vals) == 1:
                body.append("return %s;" % extra_ret_vals[0])
            else:
                body.append("return py::make_tuple(%s);"
                        % ", ".join(extra_ret_vals))

    elif meth.return_type == "void *":
        raise OddSignature("void *")

    else:
        raise NotImplementedError("ret type: %s in %s" % (meth.return_type, meth))

    outf.write("""
        %s %s_%s(%s)
        {
          %s
        }
        """ % (
            processed_return_type, meth.cls, meth.name,
            ", ".join(input_args),
            "\n".join(body)))

    return arg_names




def write_wrappers(expf, wrapf, methods):
    undoc = []

    for meth in methods:
        try:
            print meth
            arg_names = write_wrapper(wrapf, meth)
            write_exposer(expf, meth, arg_names)
        except Undocumented:
            undoc.append(str(meth))
        except OddSignature, e:
            print "SKIP (odd sig: %s): %s" % (e, meth)
        else:
            #print "WRAPPED:", meth
            pass

    print "SKIP (%d undocumented methods): %s" % (len(undoc), ", ".join(undoc))



def gen_wrapper(include_dirs):
    fdata = FunctionData(include_dirs)
    fdata.read_header("isl/dim.h")
    fdata.read_header("isl/set.h")
    fdata.read_header("isl/map.h")
    fdata.read_header("isl/vec.h")
    fdata.read_header("isl/mat.h")
    fdata.read_header("isl/local_space.h")
    fdata.read_header("isl/aff.h")
    fdata.read_header("isl/polynomial.h")
    fdata.read_header("isl/union_map.h")
    fdata.read_header("isl/union_set.h")
    fdata.read_header("isl/printer.h")
    fdata.read_header("isl/vertices.h")
    fdata.read_header("isl/constraint.h")

    expf = open("src/wrapper/gen-expose.inc", "wt")
    wrapf = open("src/wrapper/gen-wrap.inc", "wt")

    write_wrappers(expf, wrapf, [
        meth
        for methods in fdata.classes_to_methods.itervalues()
        for meth in methods])

    expf.close()
    wrapf.close()





if __name__ == "__main__":
    from os.path import expanduser
    gen_wrapper([expanduser("~/pool/include")])
