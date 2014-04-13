import re
import sys

SEM_TAKE = "take"
SEM_GIVE = "give"
SEM_KEEP = "keep"

ISL_SEM_TO_SEM = {
    "__isl_take": SEM_TAKE,
    "__isl_give": SEM_GIVE,
    "__isl_keep": SEM_KEEP,
    }

NON_COPYABLE = ["ctx", "printer", "access_info"]
NON_COPYABLE_WITH_ISL_PREFIX = ["isl_"+i for i in NON_COPYABLE]

PYTHON_RESERVED_WORDS = """
and       del       from      not       while
as        elif      global    or        with
assert    else      if        pass      yield
break     except    import    print
class     exec      in        raise
continue  finally   is        return
def       for       lambda    try
""".split()


# {{{ data model

class Argument:
    def __init__(self, name, semantics, base_type, ptr):
        self.name = name
        self.semantics = semantics
        self.base_type = base_type
        self.ptr = ptr


class CallbackArgument:
    def __init__(self, name, return_base_type, return_ptr, args):
        self.name = name
        self.return_base_type = return_base_type
        self.return_ptr = return_ptr
        self.args = args


class Method:
    def __init__(self, cls, name, c_name,
            return_semantics, return_base_type, return_ptr,
            args, is_exported, is_constructor):
        self.cls = cls
        self.name = name
        self.c_name = c_name
        self.return_semantics = return_semantics
        self.return_base_type = return_base_type
        self.return_ptr = return_ptr
        self.args = args
        self.mutator_veto = False
        self.is_exported = is_exported
        self.is_constructor = is_constructor

        if not self.is_static:
            self.args[0].name = "self"

    @property
    def is_static(self):
        return not (self.args and self.args[0].base_type.startswith("isl_"+self.cls))

    @property
    def is_mutator(self):
        return (not self.is_static
                and self.args[0].semantics is SEM_TAKE
                and self.return_ptr == "*" == self.args[0].ptr
                and self.return_base_type == self.args[0].base_type
                and self.return_semantics is SEM_GIVE
                and not self.mutator_veto
                and self.args[0].base_type in NON_COPYABLE_WITH_ISL_PREFIX)

    def __repr__(self):
        return "<method %s>" % self.c_name

# }}}


PART_TO_CLASSES = {
        # If you change this, change:
        # - src/wrapper/wrap_isl.hpp to add WRAP_CLASS(...)
        # - src/wrapper/wrap_isl_partN.hpp to add MAKE_WRAP(...)
        # - doc/reference.rst

        "part1": [
            # lists
            "id_list",
            "basic_set_list", "set_list", "aff_list", "pw_aff_list", "band_list",
            "ast_expr_list", "ast_node_list",

            # maps
            "id_to_ast_expr",

            # others
            "printer",  "val", "multi_val", "vec", "mat",
            "aff", "pw_aff",
            "multi_aff", "multi_pw_aff", "pw_multi_aff", "union_pw_multi_aff",

            "id",
            "constraint", "space", "local_space",
        ],

        "part2": [
            "basic_set", "basic_map",
            "set", "map",
            "union_map", "union_set",
            "point", "vertex", "cell", "vertices",
        ],

        "part3": [
            "qpolynomial_fold", "pw_qpolynomial_fold",
            "union_pw_qpolynomial_fold",
            "union_pw_qpolynomial",
            "qpolynomial", "pw_qpolynomial",
            "term",

            "band", "schedule", "schedule_constraints",

            "access_info", "flow", "restriction",

            "ast_expr", "ast_node", "ast_print_options",
            "ast_build",
        ]
        }
CLASSES = []
for cls_list in PART_TO_CLASSES.values():
    CLASSES.extend(cls_list)

CLASS_MAP = {
        "equality": "constraint",
        "inequality": "constraint",
        "options": "ctx",
        }

ENUMS = ["isl_dim_type", "isl_fold",
        "isl_ast_op_type", "isl_ast_expr_type",
        "isl_ast_node_type"]

SAFE_TYPES = ENUMS + ["int", "unsigned", "uint32_t", "size_t", "double",
        "long", "unsigned long"]
SAFE_IN_TYPES = SAFE_TYPES + ["const char *", "char *"]

# {{{ parser

DECL_RE = re.compile(r"""
    ((?:\w+\s+)*) (\**) \s* (?# return type)
    (\w+) (?# func name)
    \(
    (.*) (?# args)
    \)
    """,
    re.VERBOSE)
FUNC_PTR_RE = re.compile(r"""
    ((?:\w+\s+)*) (\**) \s* (?# return type)
    \(\*(\w+)\) (?# func name)
    \(
    (.*) (?# args)
    \)
    """,
    re.VERBOSE)
STRUCT_DECL_RE = re.compile(r"(__isl_export\s+)?struct\s+([a-z_A-Z0-9]+)\s*;")
ARG_RE = re.compile(r"^((?:\w+)\s+)+(\**)\s*(\w+)$")
INLINE_SEMICOLON_RE = re.compile(r"\;[ \t]*(?=\w)")


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


def split_at_unparenthesized_commas(s):
    paren_level = 0
    i = 0
    last_start = 0

    while i < len(s):
        c = s[i]
        if c == "(":
            paren_level += 1
        elif c == ")":
            paren_level -= 1
        elif c == "," and paren_level == 0:
            yield s[last_start:i]
            last_start = i+1

        i += 1

    yield s[last_start:i]


def to_py_class(cls):
    if cls.startswith("isl_"):
        cls = cls[4:]

    if cls == "ctx":
        return "Context"

    upper_next = True
    result = ""

    for c in cls:
        if c == "_":
            upper_next = True
        else:
            if upper_next:
                result += c.upper()
                upper_next = False
            else:
                result += c

    result = result.replace("Qpoly", "QPoly")

    return result


class Retry(RuntimeError):
    pass


class BadArg(ValueError):
    pass


class Undocumented(ValueError):
    pass


class SignatureNotSupported(ValueError):
    pass


def parse_arg(arg):
    if "(*" in arg:
        arg_match = FUNC_PTR_RE.match(arg)
        assert arg_match is not None, "fptr: %s" % arg

        return_base_type = arg_match.group(1)
        return_ptr = arg_match.group(2)
        name = arg_match.group(3)
        args = [parse_arg(i.strip())
                for i in split_at_unparenthesized_commas(arg_match.group(4))]

        return CallbackArgument(name.strip(),
                return_base_type.strip(), return_ptr.strip(), args)

    words = arg.split()
    semantics, words = filter_semantics(words)

    words = [w for w in words if w not in ["struct", "enum"]]

    rebuilt_arg = " ".join(words)
    arg_match = ARG_RE.match(rebuilt_arg)

    assert arg_match is not None, rebuilt_arg
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            base_type=arg_match.group(1).strip(),
            ptr=arg_match.group(2).strip())


class FunctionData:
    def __init__(self, include_dirs):
        self.classes_to_methods = {}
        self.include_dirs = include_dirs
        self.seen_c_names = set()

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

        # split at semicolons
        new_lines = []
        for l in lines:
            l = INLINE_SEMICOLON_RE.sub(";\n", l)
            new_lines.extend(l.split("\n"))

        lines = new_lines

        i = 0

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
            elif l.endswith("{"):
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
                    if decl:
                        decl += " "
                    i += 1
                    if STRUCT_DECL_RE.search(decl):
                        break

                    open_par_count = sum(1 for i in decl if i == "(")
                    close_par_count = sum(1 for i in decl if i == ")")
                    if open_par_count and open_par_count == close_par_count:
                        break
                    l = lines[i].strip()

                if not STRUCT_DECL_RE.search(decl):
                    self.parse_decl(decl)

    def parse_decl(self, decl):
        decl_match = DECL_RE.match(decl)
        if decl_match is None:
            print("WARNING: func decl regexp not matched: %s" % decl)
            return

        return_base_type = decl_match.group(1)
        return_ptr = decl_match.group(2)
        c_name = decl_match.group(3)
        args = [i.strip()
                for i in split_at_unparenthesized_commas(decl_match.group(4))]

        if c_name in ["ISL_ARG_DECL", "ISL_DECLARE_MULTI",
                "ISL_DECLARE_LIST", "isl_ast_op_type_print_macro"]:
            return

        assert c_name.startswith("isl_"), c_name
        name = c_name[4:]

        found_class = False
        for cls in CLASSES:
            if name.startswith(cls):
                found_class = True
                break

        if found_class:
            name = name[len(cls)+1:]

        # Don't be tempted to chop off "_val"--the "_val" versions of
        # some methods are incompatible with the isl_int ones.
        #
        # (For example, isl_aff_get_constant() returns just the constant,
        # but isl_aff_get_constant_val() returns the constant divided by
        # the denominator.)
        #
        # To avoid breaking user code in non-obvious ways, the new
        # names are carried over to the Python level.

        if not found_class:
            for fake_cls, cls in CLASS_MAP.items():
                if name.startswith(fake_cls):
                    found_class = True
                    break

        assert found_class, name

        if name in ["free", "cow", "dump"]:
            return

        try:
            args = [parse_arg(arg) for arg in args]
        except BadArg:
            print("SKIP: %s %s" % (cls, name))
            return

        if name in PYTHON_RESERVED_WORDS:
            name = name + "_"

        if cls == "options":
            assert name.startswith("set_") or name.startswith("get_")
            name = name[:4]+"option_"+name[4:]

        words = return_base_type.split()

        is_exported = "__isl_export" in words
        if is_exported:
            words.remove("__isl_export")

        is_constructor = "__isl_constructor" in words
        if is_constructor:
            words.remove("__isl_constructor")

        return_semantics, words = filter_semantics(words)
        words = [w for w in words if w not in ["struct", "enum"]]
        return_base_type = " ".join(words)

        cls_meth_list = self.classes_to_methods.setdefault(cls, [])

        if c_name in self.seen_c_names:
            return

        cls_meth_list.append(Method(
                cls, name, c_name,
                return_semantics, return_base_type, return_ptr,
                args, is_exported=is_exported, is_constructor=is_constructor))

        self.seen_c_names.add(c_name)

# }}}


def get_callback(cb_name, cb):
    body = []
    passed_args = []

    assert cb.args[-1].name == "user"

    for arg in cb.args[:-1]:
        if arg.base_type.startswith("isl_"):
            if arg.ptr != "*":
                raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                    arg.base_type, arg.ptr))
            arg_cls = arg.base_type[4:]

            if arg.semantics is not SEM_TAKE:
                raise SignatureNotSupported("non-take callback arg")

            passed_args.append("arg_%s" % arg.name)

            body.append("""
                std::auto_ptr<%(arg_cls)s> wrapped_arg_%(name)s(
                    new %(arg_cls)s(c_arg_%(name)s));
                py::object arg_%(name)s(
                    handle_from_new_ptr(wrapped_arg_%(name)s.get()));
                wrapped_arg_%(name)s.release();
                """ % dict(
                    arg_cls=arg_cls,
                    name=arg.name,
                    ))
        else:
            raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                arg.base_type, arg.ptr))

    return """
        static %(ret_type)s %(cb_name)s(%(input_args)s)
        {
            py::object &py_cb = *reinterpret_cast<py::object *>(c_arg_user);
            try
            {
              %(body)s
              py::object retval = py_cb(%(passed_args)s);
              if (retval.ptr() == Py_None)
                return 0;
              else
                return py::extract<%(ret_type)s>(retval);
            }
            catch (py::error_already_set)
            {
              std::cout << "[islpy warning] A Python exception occurred in "
                "a call back function, ignoring:" << std::endl;
              PyErr_Print();
              return -1;
            }
            catch (std::exception &e)
            {
              std::cerr << "[islpy] An exception occurred in "
                "a Python callback query:" << std::endl
                << e.what() << std::endl;
              std::cout << "[islpy] Aborting now." << std::endl;
              return -1;
            }
        }
        """ % dict(
                ret_type="%s %s" % (cb.return_base_type, cb.return_ptr),
                cb_name=cb_name,
                input_args=
                ", ".join("%s %sc_arg_%s" % (arg.base_type, arg.ptr, arg.name)
                    for arg in cb.args),
                body="\n".join(body),
                passed_args=", ".join(passed_args))


# {{{ wrapper generator

def write_wrapper(outf, meth):
    body = []
    checks = []
    docs = []

    passed_args = []
    input_args = []
    post_call = []
    extra_ret_vals = []
    extra_ret_descrs = []
    preamble = []

    arg_names = []

    arg_idx = 0
    while arg_idx < len(meth.args):
        arg = meth.args[arg_idx]
        arg_names.append(arg.name)

        if isinstance(arg, CallbackArgument):
            if not (arg.return_base_type in SAFE_IN_TYPES and not arg.return_ptr):
                raise SignatureNotSupported("non-int callback")

            arg_names.pop()
            arg_idx += 1
            if meth.args[arg_idx].name != "user":
                raise SignatureNotSupported("unexpected callback signature")

            cb_name = "cb_%s_%s_%s" % (meth.cls, meth.name, arg.name)

            input_args.append("py::object py_%s" % arg.name)
            passed_args.append(cb_name)
            passed_args.append("&py_%s" % arg.name)

            preamble.append(get_callback(cb_name, arg))

            docs.append(":param %s: callback(%s)"
                    % (arg.name, ", ".join(
                        sub_arg.name
                        for sub_arg in arg.args
                        if sub_arg.name != "user")))

        elif arg.base_type in SAFE_IN_TYPES and not arg.ptr:
            passed_args.append("arg_"+arg.name)
            input_args.append("%s arg_%s" % (arg.base_type, arg.name))

            doc_cls = arg.base_type
            if doc_cls.startswith("isl_"):
                doc_cls = doc_cls[4:]

            docs.append(":param %s: :class:`%s`" % (arg.name, doc_cls))

        elif arg.base_type in ["char", "const char"] and arg.ptr == "*":
            if arg.semantics is SEM_KEEP:
                passed_args.append("strdup(%s)" % arg.name)
            else:
                passed_args.append(arg.name)
            input_args.append("%s *%s" % (arg.base_type, arg.name))

            docs.append(":param %s: string" % arg.name)

        elif arg.base_type == "int" and arg.ptr == "*":
            if arg.name in ["exact", "tight"]:
                body.append("int arg_%s;" % arg.name)
                passed_args.append("&arg_%s" % arg.name)
                extra_ret_vals.append("arg_%s" % arg.name)
                extra_ret_descrs.append("%s (integer)" % arg.name)
                arg_names.pop()
            else:
                raise SignatureNotSupported("int *")

        elif arg.base_type == "isl_val" and arg.ptr == "*" and arg_idx > 0:
            # {{{ val input argument

            arg_descr = ":param %s: :class:`Val`" % arg.name
            input_args.append("py::object py_%s" % arg.name)
            checks.append("""
                std::auto_ptr<val> auto_arg_%(name)s;
                py::extract<val *> ex_%(name)s(py_%(name)s);
                isl_ctx *ctx_for_%(name)s =
                    %(first_arg_base_type)s_get_ctx(arg_%(first_arg)s.m_data);

                if (ex_%(name)s.check())
                {
                  val *arg_%(name)s = ex_%(name)s();
                  if (!auto_arg_%(name)s->is_valid())
                    throw isl::error(
                      "passed invalid val for %(name)s");

                  isl_val *tmp_ptr = isl_val_copy(arg_%(name)s->m_data);
                  if (!tmp_ptr)
                      throw isl::error("failed to copy arg %(name)s");
                  auto_arg_%(name)s = std::auto_ptr<val>(new val(tmp_ptr));
                }
                else if (PyLong_Check(py_%(name)s.ptr()))
                {
                  long value = PyLong_AsLong(py_%(name)s.ptr());
                  if (PyErr_Occurred())
                    throw py::error_already_set();

                  isl_val *tmp_ptr = isl_val_int_from_si(ctx_for_%(name)s, value);
                  if (!tmp_ptr)
                      throw isl::error("failed to create arg %(name)s from integer");
                  auto_arg_%(name)s = std::auto_ptr<val>(new val(tmp_ptr));
                }
                """ % dict(
                    name=arg.name,
                    first_arg_base_type=meth.args[0].base_type,
                    first_arg=meth.args[0].name,
                    ))

            if sys.version_info < (3,):
                checks.append("""
                    else if (PyInt_Check(py_%(name)s.ptr()))
                    {
                      isl_val *tmp_ptr = isl_val_int_from_si(ctx_for_%(name)s,
                          PyInt_AsLong(py_%(name)s.ptr()));
                      if (!tmp_ptr)
                          throw isl::error("failed to create arg "
                              "%(name)s from integer");
                      auto_arg_%(name)s = std::auto_ptr<val>(new val(tmp_ptr));
                    }
                    """ % dict(
                        name=arg.name,
                        ))

            checks.append("""
                else
                {
                  throw isl::error("unrecognized argument for %(name)s");
                }
                """ % dict(
                    name=arg.name,
                    ))

            if arg.semantics is None and arg.base_type != "isl_ctx":
                raise Undocumented(meth)

            if arg.semantics is SEM_TAKE:
                post_call.append("auto_arg_%s.release();" % arg.name)

            passed_args.append("auto_arg_%s->m_data" % arg.name)
            docs.append(arg_descr)

            # }}}

        elif arg.base_type.startswith("isl_") and arg.ptr == "*":
            # {{{ isl types input arguments

            need_nonconst = False

            arg_cls = arg.base_type[4:]
            arg_descr = ":param %s: :class:`%s`" % (arg.name, to_py_class(arg_cls))

            if arg.semantics is None and arg.base_type != "isl_ctx":
                raise Undocumented(meth)

            checks.append("""
                if (!arg_%(name)s.is_valid())
                  throw isl::error(
                    "passed invalid arg to isl_%(meth)s for %(name)s");
                """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))

            copyable = arg_cls not in NON_COPYABLE
            if arg.semantics is SEM_TAKE:
                if copyable:
                    checks.append("""
                        if (!arg_%(name)s.is_valid())
                          throw isl::error(
                            "passed invalid arg to isl_%(meth)s for %(name)s");
                        std::auto_ptr<%(cls)s> auto_arg_%(name)s;
                        {
                            isl_%(cls)s *tmp_ptr =
                                isl_%(cls)s_copy(arg_%(name)s.m_data);
                            if (!tmp_ptr)
                                throw isl::error("failed to copy arg "
                                    "%(name)s on entry to %(meth)s");
                            auto_arg_%(name)s = std::auto_ptr<%(cls)s>(
                                new %(cls)s(tmp_ptr));
                        }
                        """ % dict(
                            name=arg.name,
                            meth="%s_%s" % (meth.cls, meth.name),
                            cls=arg_cls))

                    post_call.append("auto_arg_%s.release();" % arg.name)
                    passed_args.append("auto_arg_%s->m_data" % arg.name)

                else:
                    need_nonconst = True

                    if not (arg_idx == 0 and meth.is_mutator):
                        post_call.append("arg_%s.invalidate();" % arg.name)

                    passed_args.append("arg_%s.m_data" % arg.name)

                    if arg_idx == 0 and meth.is_mutator:
                        arg_descr += " (mutated in-place)"
                    else:
                        arg_descr += " (:ref:`becomes invalid <auto-invalidation>`)"
            else:
                passed_args.append("arg_%s.m_data" % arg.name)

            if need_nonconst:
                input_args.append("%s &%s" % (arg_cls, "arg_"+arg.name))
            else:
                input_args.append("%s const &%s" % (arg_cls, "arg_"+arg.name))

            docs.append(arg_descr)

            # }}}

        elif arg.base_type.startswith("isl_") and arg.ptr == "**":
            # {{{ isl types output arguments

            if arg.semantics is not SEM_GIVE:
                raise SignatureNotSupported("non-give secondary ptr return value")

            ret_cls = arg.base_type[4:]

            arg_names.pop()
            body.append("%s *ret_%s;" % (arg.base_type, arg.name))
            passed_args.append("&ret_%s" % arg.name)

            post_call.append("""
                py::object py_ret_%(name)s;
                if (ret_%(name)s)
                {
                  std::auto_ptr<%(ret_cls)s> auto_ret_%(name)s(
                    new %(ret_cls)s(ret_%(name)s));
                  py_ret_%(name)s = py::object(
                    handle_from_new_ptr(auto_ret_%(name)s.get()));
                  auto_ret_%(name)s.release();
                }
                """ % dict(name=arg.name, ret_cls=ret_cls))

            extra_ret_vals.append("py_ret_%s" % arg.name)
            extra_ret_descrs.append(
                    "%s (:class:`%s`)" % (arg.name, to_py_class(ret_cls)))

            # }}}

        elif arg.base_type == "FILE" and arg.ptr == "*":
            if sys.version_info >= (3,):
                raise SignatureNotSupported(
                        "arg type %s %s" % (arg.base_type, arg.ptr))

            passed_args.append("PyFile_AsFile(arg_%s.ptr())" % arg.name)
            input_args.append("py::object %s" % ("arg_"+arg.name))
            docs.append(":param %s: :class:`file`-like "
                    "(NOTE: This will cease to be supported in Python 3.)"
                    % arg.name)

        elif (arg.base_type == "void"
                and arg.ptr == "*"
                and arg.name == "user"):
            body.append("Py_INCREF(arg_%s.ptr());" % arg.name)
            passed_args.append("arg_%s.ptr()" % arg.name)
            input_args.append("py::object %s" % ("arg_"+arg.name))
            post_call.append("""
                isl_%s_set_free_user(result, my_decref);
                """ % meth.cls)
            docs.append(":param %s: a user-specified Python object" % arg.name)

        else:
            raise SignatureNotSupported("arg type %s %s" % (arg.base_type, arg.ptr))

        arg_idx += 1

    processed_return_type = "%s %s" % (meth.return_base_type, meth.return_ptr)

    if meth.return_base_type == "void" and not meth.return_ptr:
        result_capture = ""
    else:
        result_capture = "%s %sresult = " % (meth.return_base_type, meth.return_ptr)

    body = checks + body

    body.append("%s%s(%s);" % (
        result_capture, meth.c_name, ", ".join(passed_args)))

    body += post_call

    # {{{ return value processing

    if meth.return_base_type == "int" and not meth.return_ptr:
        body.append("""
            if (result == -1)
            {
              throw isl::error("call to isl_%(cls)s_%(name)s failed");
            }""" % {"cls": meth.cls, "name": meth.name})

        if meth.name.startswith("is_") or meth.name.startswith("has_"):
            processed_return_type = "bool"

        ret_descr = processed_return_type

        if extra_ret_vals:
            if len(extra_ret_vals) == 1:
                processed_return_type = "py::object"
                body.append("return py::object(%s);" % extra_ret_vals[0])
                ret_descr = extra_ret_descrs[0]
            else:
                processed_return_type = "py::object"
                body.append("return py::make_tuple(%s);" % ", ".join(extra_ret_vals))
                ret_descr = "tuple: (%s)" % (", ".join(extra_ret_descrs))
        else:
            body.append("return result;")

    elif meth.return_base_type in SAFE_TYPES and not meth.return_ptr:
        if extra_ret_vals:
            raise NotImplementedError("extra ret val with safe type")

        body.append("return result;")
        ret_descr = processed_return_type

    elif meth.return_base_type.startswith("isl_"):
        assert meth.return_ptr == "*", meth

        ret_cls = meth.return_base_type[4:]

        if meth.is_mutator:
            if extra_ret_vals:
                meth.mutator_veto = True
                raise Retry()

            processed_return_type = "isl::%s &" % ret_cls
            body.append("arg_%s.m_data = result;" % meth.args[0].name)
            body.append("return arg_%s;" % meth.args[0].name)

            ret_descr = ":class:`%s` (self)" % to_py_class(ret_cls)
        else:
            processed_return_type = "py::object"
            isl_obj_ret_val = \
                    "py::object(handle_from_new_ptr(new %s(result)))" % ret_cls

            if extra_ret_vals:
                isl_obj_ret_val = "py::make_tuple(%s, %s)" % (
                        isl_obj_ret_val, ", ".join(extra_ret_vals))
                ret_descr = "tuple: (:class:`%s`, %s)" % (
                        to_py_class(ret_cls), ", ".join(extra_ret_descrs))
            else:
                ret_descr = ":class:`%s`" % to_py_class(ret_cls)

            if meth.return_semantics is None and ret_cls != "ctx":
                raise Undocumented(meth)

            if meth.return_semantics is not SEM_GIVE and ret_cls != "ctx":
                raise SignatureNotSupported("non-give return")

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
                  throw isl::error("call to isl_%(cls)s_%(name)s failed");
                }
                """ % {
                    "ret_cls": ret_cls,
                    "ret_val": isl_obj_ret_val,
                    "cls": meth.cls,
                    "name": meth.name,
                    })

    elif meth.return_base_type in ["const char", "char"] and meth.return_ptr == "*":
        if extra_ret_vals:
            raise NotImplementedError("extra ret val with string")

        processed_return_type = "py::object"
        body.append("""
            if (result)
              return py::object(std::string(result));
            else
              return py::object();
            """)
        if meth.return_semantics is SEM_GIVE:
            body.append("free(result);")

        ret_descr = "string"

    elif (meth.return_base_type == "void"
            and meth.return_ptr == "*"
            and meth.name == "get_user"):

        body.append("""
            return py::object(py::handle<>(py::borrowed((PyObject *) result)));
            """)
        ret_descr = "a user-specified python object"
        processed_return_type = "py::object"

    elif meth.return_base_type == "void" and not meth.return_ptr:
        if extra_ret_vals:
            processed_return_type = "py::object"
            if len(extra_ret_vals) == 1:
                body.append("return %s;" % extra_ret_vals[0])
                ret_descr = extra_ret_descrs[0]
            else:
                body.append("return py::make_tuple(%s);"
                        % ", ".join(extra_ret_vals))
                ret_descr = "tuple: " + ", ".join(extra_ret_descrs)
        else:
            ret_descr = "None"

    else:
        raise SignatureNotSupported("ret type: %s %s in %s" % (
            meth.return_base_type, meth.return_ptr, meth))

    # }}}

    outf.write("""
        %s
        %s %s_%s(%s)
        {
          %s
        }
        """ % (
            "\n".join(preamble),
            processed_return_type, meth.cls, meth.name,
            ", ".join(input_args),
            "\n".join(body)))

    docs = (["%s(%s)" % (meth.name, ", ".join(arg_names)), ""]
            + docs
            + [":return: %s" % ret_descr])

    return arg_names, "\n".join(docs)

# }}}


# {{{ exposer generator

def write_exposer(outf, meth, arg_names, doc_str, static_decls):
    func_name = "isl::%s_%s" % (meth.cls, meth.name)
    py_name = meth.name

    args_str = (", py::args(%s)"
            % ", ".join('"%s"' % arg_name for arg_name in arg_names))

    if meth.name == "size" and len(meth.args) == 1:
        py_name = "__len__"

    if meth.name == "get_hash" and len(meth.args) == 1:
        py_name = "__hash__"

    extra_py_names = []

    #if meth.is_static:
        #doc_str = "(static method)\n" + doc_str

    doc_str_arg = ", \"%s\"" % doc_str.replace("\n", "\\n")

    extra_stuff = args_str+doc_str_arg
    if meth.is_mutator:
        extra_stuff = extra_stuff+", py::return_self<>()"

    wrap_class = CLASS_MAP.get(meth.cls, meth.cls)

    for exp_py_name in [py_name]+extra_py_names:
        outf.write("wrap_%s.def(\"%s\", %s%s);\n" % (
            wrap_class, exp_py_name, func_name, extra_stuff))
        if meth.is_static:
            static_decls.append("wrap_%s.staticmethod(\"%s\");\n" % (
                wrap_class, exp_py_name))

# }}}


def write_wrappers(expf, wrapf, methods):
    undoc = []
    static_decls = []

    for meth in methods:
        #print "TRY_WRAP:", meth
        if meth.name.endswith("_si") or meth.name.endswith("_ui"):
            val_versions = [
                    meth2
                    for meth2 in methods
                    if meth2.cls == meth.cls
                    and (
                        meth2.name == meth.name[:-3]
                        or meth2.name == meth.name[:-3] + "_val"
                        )
                    ]

            if val_versions:
                # no need to expose C integer versions of things
                print("SKIP (val version available): %s -> %s"
                        % (meth, ", ".join(str(s) for s in val_versions)))
                continue

        try:
            arg_names, doc_str = write_wrapper(wrapf, meth)
            write_exposer(expf, meth, arg_names, doc_str, static_decls)
        except Undocumented:
            undoc.append(str(meth))
        except Retry:
            arg_names, doc_str = write_wrapper(wrapf, meth)
            write_exposer(expf, meth, arg_names, doc_str, static_decls)
        except SignatureNotSupported:
            _, e, _ = sys.exc_info()
            print("SKIP (sig not supported: %s): %s" % (e, meth))
        else:
            #print "WRAPPED:", meth
            pass

    for static_decl in static_decls:
        expf.write(static_decl)

    print("SKIP (%d undocumented methods): %s" % (len(undoc), ", ".join(undoc)))


def gen_wrapper(include_dirs):
    fdata = FunctionData(["."] + include_dirs)
    fdata.read_header("isl_declaration_macros_expanded.h")
    fdata.read_header("isl/id.h")
    fdata.read_header("isl/space.h")
    fdata.read_header("isl/set.h")
    fdata.read_header("isl/map.h")
    fdata.read_header("isl/local_space.h")
    fdata.read_header("isl/aff.h")
    fdata.read_header("isl/polynomial.h")
    fdata.read_header("isl/union_map.h")
    fdata.read_header("isl/union_set.h")
    fdata.read_header("isl/printer.h")
    fdata.read_header("isl/vertices.h")
    fdata.read_header("isl/point.h")
    fdata.read_header("isl/constraint.h")
    fdata.read_header("isl/val.h")
    fdata.read_header("isl/vec.h")
    fdata.read_header("isl/mat.h")
    fdata.read_header("isl/band.h")
    fdata.read_header("isl/schedule.h")
    fdata.read_header("isl/flow.h")
    fdata.read_header("isl/options.h")
    fdata.read_header("isl/ast.h")
    fdata.read_header("isl/ast_build.h")

    for part, classes in PART_TO_CLASSES.items():
        expf = open("src/wrapper/gen-expose-%s.inc" % part, "wt")
        wrapf = open("src/wrapper/gen-wrap-%s.inc" % part, "wt")

        write_wrappers(expf, wrapf, [
            meth
            for cls in classes
            for meth in fdata.classes_to_methods.get(cls, [])])

        expf.close()
        wrapf.close()


if __name__ == "__main__":
    from os.path import expanduser
    gen_wrapper([expanduser("isl/include")])

# vim: foldmethod=marker
