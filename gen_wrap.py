from __future__ import print_function
import re
import sys
from py_codegen import PythonCodeGenerator, Indentation

SEM_TAKE = "take"
SEM_GIVE = "give"
SEM_KEEP = "keep"
SEM_NULL = "null"

ISL_SEM_TO_SEM = {
    "__isl_take": SEM_TAKE,
    "__isl_give": SEM_GIVE,
    "__isl_keep": SEM_KEEP,
    "__isl_null": SEM_NULL,
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

    def c_declarator(self):
        return "{type} {ptr}{name}".format(
                type=self.base_type,
                ptr=self.ptr,
                name=self.name)


class CallbackArgument:
    def __init__(self, name, return_semantics, return_base_type, return_ptr, args):
        self.name = name
        self.return_semantics = return_semantics
        self.return_base_type = return_base_type
        self.return_ptr = return_ptr
        self.args = args

    def c_declarator(self):
        return "{type} {ptr}(*{name})({args})".format(
                type=self.return_base_type,
                ptr=self.return_ptr,
                name=self.name,
                args=", ".join(arg.c_declarator() for arg in self.args))


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


CLASSES = [
        "options",
        "ctx",

        # lists
        "id_list", "val_list",
        "basic_set_list", "basic_map_list", "set_list", "map_list",
        "union_set_list",
        "constraint_list",
        "aff_list", "pw_aff_list", "band_list",
        "ast_expr_list", "ast_node_list",

        # maps
        "id_to_ast_expr",

        # others
        "printer",  "val", "multi_val", "vec", "mat",
        "aff", "pw_aff", "union_pw_aff",
        "multi_aff", "multi_pw_aff", "pw_multi_aff", "union_pw_multi_aff",
        "multi_union_pw_aff",

        "id",
        "constraint", "space", "local_space",

        "basic_set", "basic_map",
        "set", "map",
        "union_map", "union_set",
        "point", "vertex", "cell", "vertices",

        "qpolynomial_fold", "pw_qpolynomial_fold",
        "union_pw_qpolynomial_fold",
        "union_pw_qpolynomial",
        "qpolynomial", "pw_qpolynomial",
        "term",

        "band", "schedule", "schedule_constraints",
        "schedule_node",

        "access_info", "flow", "restriction",
        "union_access_info", "union_flow",

        "ast_expr", "ast_node", "ast_print_options",
        "ast_build",
        ]


IMPLICIT_CONVERSIONS = {
    "isl_set": [("isl_basic_set", "from_basic_set")],
    "isl_map": [("isl_basic_map", "from_basic_map")],
    "isl_union_set": [("isl_set", "from_set")],
    "isl_union_map": [("isl_map", "from_map")],
    "isl_local_space": [("isl_space", "from_space")],
    "isl_pw_aff": [("isl_aff", "from_aff")],
    }


HEADER_PREAMBLE = """
// ctx.h
typedef enum {
        isl_error_none = 0,
        isl_error_abort,
        isl_error_alloc,
        isl_error_unknown,
        isl_error_internal,
        isl_error_invalid,
        isl_error_quota,
        isl_error_unsupported
} isl_error;

typedef enum {
        isl_stat_error = -1,
        isl_stat_ok = 0,
} isl_stat;

typedef enum {
        isl_bool_error = -1,
        isl_bool_false = 0,
        isl_bool_true = 1
} isl_bool;

// space.h
typedef enum {
        isl_dim_cst,
        isl_dim_param,
        isl_dim_in,
        isl_dim_out,
        isl_dim_set = isl_dim_out,
        isl_dim_div,
        isl_dim_all
} isl_dim_type;

// ast_type.h
typedef enum {
        isl_ast_op_error = -1,
        isl_ast_op_and,
        isl_ast_op_and_then,
        isl_ast_op_or,
        isl_ast_op_or_else,
        isl_ast_op_max,
        isl_ast_op_min,
        isl_ast_op_minus,
        isl_ast_op_add,
        isl_ast_op_sub,
        isl_ast_op_mul,
        isl_ast_op_div,
        isl_ast_op_fdiv_q,      /* Round towards -infty */
        isl_ast_op_pdiv_q,      /* Dividend is non-negative */
        isl_ast_op_pdiv_r,      /* Dividend is non-negative */
        isl_ast_op_zdiv_r,      /* Result only compared against zero */
        isl_ast_op_cond,
        isl_ast_op_select,
        isl_ast_op_eq,
        isl_ast_op_le,
        isl_ast_op_lt,
        isl_ast_op_ge,
        isl_ast_op_gt,
        isl_ast_op_call,
        isl_ast_op_access,
        isl_ast_op_member,
        isl_ast_op_address_of
} isl_ast_op_type;

typedef enum {
        isl_ast_expr_error = -1,
        isl_ast_expr_op,
        isl_ast_expr_id,
        isl_ast_expr_int
} isl_ast_expr_type ;

typedef enum {
        isl_ast_node_error = -1,
        isl_ast_node_for = 1,
        isl_ast_node_if,
        isl_ast_node_block,
        isl_ast_node_mark,
        isl_ast_node_user
} isl_ast_node_type;

typedef enum {
        isl_ast_loop_error = -1,
        isl_ast_loop_default = 0,
        isl_ast_loop_atomic,
        isl_ast_loop_unroll,
        isl_ast_loop_separate
} isl_ast_loop_type;

// flow.h
typedef int (*isl_access_level_before)(void *first, void *second);
typedef isl_restriction *(*isl_access_restrict)(
        isl_map *source_map, isl_set *sink,
        void *source_user, void *user);

// polynomial_type.h
typedef enum {
        isl_fold_min,
        isl_fold_max,
        isl_fold_list
} isl_fold;
"""

PY_PREAMBLE = """
from __future__ import print_function

import six


from islpy._isl_cffi import ffi
lib = ffi.dlopen("libisl.so.13")

from cffi import FFI
libc_ffi = FFI()
libc_ffi.cdef('''
    char *strdup(const char *s);
    void free(void *ptr);
    ''')

libc = libc_ffi.dlopen(None)


class Error(StandardError):
    pass


class IslTypeError(Error, TypeError):
    pass

_context_use_map = {}

def _deref_ctx(ctx_data, ctx_iptr):
    _context_use_map[ctx_iptr] -= 1
    if not _context_use_map[ctx_iptr]:
        del _context_use_map[ctx_iptr]
        lib.isl_ctx_free(ctx_data)


class _ISLObjectBase(object):
    def _setup(self, data):
        assert not hasattr(self, "data")
        assert isinstance(data, ffi.CData)
        self.data =  data

        self._set_ctx_data()
        iptr = self._ctx_iptr
        _context_use_map[iptr] = _context_use_map.get(iptr, 0) + 1

    def _reset(self, data):
        assert self.data is not None
        assert isinstance(data, ffi.CData)

        _deref_ctx(self._ctx_data, self._ctx_iptr)
        self.data = data

        self._set_ctx_data()
        iptr = self._ctx_iptr
        _context_use_map[iptr] = _context_use_map.get(iptr, 0) + 1

    def _set_ctx_data(self):
        self._ctx_data = self._get_ctx_data()
        self._ctx_iptr = int(ffi.cast("intptr_t", self._get_ctx_data()))

    def _release(self):
        if self.data is None:
            raise Error("cannot release already-released object")

        data = self.data
        if _deref_ctx is not None:
            _deref_ctx(self._ctx_data, self._ctx_iptr)
        else:
            # This can happen if we're called super-late in cleanup.
            # Since everything else is already mopped up, we really
            # can't do what it takes to mop up this context.
            # So we leak it (i.e. leave it for the OS to clean up.)
            pass

        self.data = None
        return data


def _instantiate(cls, data):
    result = _ISLObjectBase.__new__(_ISLObjectBase)
    result.__class__ = cls
    result._setup(data)
    return result


class _ManagedCString(object):
    def __init__(self, cdata):
        self.data = libc.strdup(cdata)
        if self.data == libc_ffi.NULL:
            raise Error("strdup() failed")

    def release(self):
        if self.data is None:
            raise Error("cannot release already-released object")

        data = self.data
        self.data = None
        return data

    def __del__(self):
        libc.free(self.data)
"""

CLASS_MAP = {
        "equality": "constraint",
        "inequality": "constraint",
        "options": "ctx",
        }

ENUMS = ["isl_dim_type", "isl_fold",
        "isl_ast_op_type", "isl_ast_expr_type",
        "isl_ast_node_type", "isl_stat", "isl_error"]

SAFE_TYPES = ENUMS + ["int", "unsigned", "uint32_t", "size_t", "double",
        "long", "unsigned long"]
SAFE_IN_TYPES = SAFE_TYPES + ["const char *", "char *"]


SPECIAL_CLASS_NAME_MAP = {
        "ctx": "Context"
        }


def isl_class_to_py_class(cls_name):
    if cls_name.startswith("isl_"):
        cls_name = cls_name[4:]

    try:
        return SPECIAL_CLASS_NAME_MAP[cls_name]
    except KeyError:
        result = cls_name.title().replace("_", "")
        result = result.replace("Qpoly", "QPoly")
        return result


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


class BadArg(ValueError):
    pass


class Retry(ValueError):
    pass


class Undocumented(ValueError):
    pass


class SignatureNotSupported(ValueError):
    pass


def parse_arg(arg):
    if "(*" in arg:
        arg_match = FUNC_PTR_RE.match(arg)
        assert arg_match is not None, "fptr: %s" % arg

        return_semantics, ret_words = filter_semantics(
                arg_match.group(1).split())
        ret_words = [w for w in ret_words if w not in ["struct", "enum"]]
        return_base_type, = ret_words

        return_ptr = arg_match.group(2)
        name = arg_match.group(3)
        args = [parse_arg(i.strip())
                for i in split_at_unparenthesized_commas(arg_match.group(4))]

        return CallbackArgument(name.strip(),
                return_semantics,
                return_base_type,
                return_ptr.strip(),
                args)

    words = arg.split()
    semantics, words = filter_semantics(words)

    words = [w for w in words if w not in ["struct", "enum"]]

    rebuilt_arg = " ".join(words)
    arg_match = ARG_RE.match(rebuilt_arg)

    base_type = arg_match.group(1).strip()

    if base_type == "isl_args":
        raise BadArg("isl_args not supported")

    assert arg_match is not None, rebuilt_arg
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            base_type=base_type,
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

        # heed continuations, split at semicolons
        new_lines = []
        i = 0
        while i < len(lines):
            my_line = lines[i].strip()
            i += 1

            while my_line.endswith("\\"):
                my_line = my_line[:-1] + lines[i].strip()
                i += 1

            if not my_line.strip().startswith("#"):
                my_line = INLINE_SEMICOLON_RE.sub(";\n", my_line)
                new_lines.extend(my_line.split("\n"))

        lines = new_lines

        i = 0

        while i < len(lines):
            l = lines[i].strip()

            if (not l
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
        return_base_type = return_base_type.replace("ISL_DEPRECATED", "").strip()

        return_ptr = decl_match.group(2)
        c_name = decl_match.group(3)
        args = [i.strip()
                for i in split_at_unparenthesized_commas(decl_match.group(4))]

        if args == ["void"]:
            args = []

        if c_name in [
                "ISL_ARG_DECL",
                "ISL_DECLARE_LIST",
                "ISL_DECLARE_LIST_FN",
                "isl_ast_op_type_print_macro",
                "ISL_DECLARE_MULTI",
                "ISL_DECLARE_MULTI_NEG",
                "ISL_DECLARE_MULTI_DIMS",
                "ISL_DECLARE_MULTI_WITH_DOMAIN",
                "isl_malloc_or_die",
                "isl_calloc_or_die",
                "isl_realloc_or_die",
                "isl_handle_error",
                ]:
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

        if name.startswith("2"):
            name = "two_"+name[1:]

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


# {{{ header writer

def write_classes_to_header(header_f):
    for cls_name in CLASSES:
        header_f.write("struct isl_{name}_struct;\n".format(name=cls_name))
        header_f.write(
                "typedef struct isl_{name}_struct isl_{name};\n"
                .format(name=cls_name))


def write_method_header(header_f, method):
    header_f.write(
            "{ret_type} {ret_ptr}{name}({args});\n"
            .format(
                ret_type=method.return_base_type,
                ret_ptr=method.return_ptr,
                name=method.c_name,
                args=", ".join(arg.c_declarator() for arg in method.args)))

# }}}


# {{{ python wrapper writer

def write_classes_to_wrapper(wrapper_f):
    gen = PythonCodeGenerator()

    gen("# {{{ declare classes")
    gen("")
    for cls_name in CLASSES:
        py_cls = isl_class_to_py_class(cls_name)
        gen("class {cls}(_ISLObjectBase):".format(cls=py_cls))
        with Indentation(gen):
            gen("_base_name = "+repr(cls_name))
            gen("")

            if cls_name == "ctx":
                gen("""
                    def _get_ctx_data(self):
                        return self.data

                    def __del__(self):
                        if self.data is not None:
                            self._release()
                    """)
                gen("")

            else:
                gen("""
                    def _get_ctx_data(self):
                        return lib.isl_{cls}_get_ctx(self.data)

                    def __del__(self):
                        if self.data is not None:
                            lib.isl_{cls}_free(self.data)
                            _deref_ctx(self._ctx_data, self._ctx_iptr)
                    """
                    .format(cls=cls_name))
                gen("")

            if cls_name not in NON_COPYABLE:
                gen("""
                    def _copy(self):
                        assert self.data is not None

                        data = lib.isl_{cls}_copy(self.data)
                        if data == ffi.NULL:
                            raise Error("failed to copy instance of {py_cls}")

                        return _instantiate({py_cls}, data)
                    """
                    .format(cls=cls_name, py_cls=py_cls))

                gen("")

    gen("")
    gen("# }}}")
    gen("")
    gen("")

    wrapper_f.write(gen.get())


def gen_conversions(gen, tgt_cls, name):
    conversions = IMPLICIT_CONVERSIONS.get(tgt_cls, [])
    for src_cls, conversion_method in conversions:
        gen_conversions(gen, src_cls, name)

        gen("""
            if isinstance({name}, {py_src_cls}):
                {name} = {py_cls}.{conversion_method}({name})
            """
            .format(
                name=name,
                py_src_cls=isl_class_to_py_class(src_cls),
                py_cls=isl_class_to_py_class(tgt_cls),
                conversion_method=conversion_method))


def gen_callback_wrapper(gen, cb, func_name):
    passed_args = []
    input_args = []

    assert cb.args[-1].name == "user"

    pre_call = PythonCodeGenerator()
    post_call = PythonCodeGenerator()

    for arg in cb.args[:-1]:
        if arg.base_type.startswith("isl_") and arg.ptr == "*":
            input_args.append(arg.name)
            passed_args.append("_py_%s" % arg.name)

            pre_call(
                    "_py_{name} = _instantiate({py_cls}, {name})"
                    .format(
                        name=arg.name,
                        py_cls=isl_class_to_py_class(arg.base_type)))

            if arg.semantics is SEM_TAKE:
                pass
            elif arg.semantics is SEM_KEEP:
                post_call("_py_{name}._release()".format(name=arg.name))
            else:
                raise SignatureNotSupported(
                        "callback arg semantics not understood: %s" % arg.semantics)

        else:
            raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                arg.base_type, arg.ptr))

    input_args.append("user")

    gen(
            "def {func_name}({input_args}):"
            .format(
                func_name=func_name,
                input_args=", ".join(input_args)))

    with Indentation(gen):
        gen("try:")
        with Indentation(gen):
            gen.extend(pre_call)

            gen(
                    "_result = {name}({passed_args})"
                    .format(name=cb.name, passed_args=", ".join(passed_args)))

            gen("return lib.isl_stat_ok")
            gen("")

        gen("""
            except Exception as e:
                import sys
                print("[WARNING] An exception occurred in a callback function."
                    "This exception was ignored.", file=sys.stderr)
                import traceback
                traceback.print_exc()

                return lib.isl_stat_error
            """)

    gen("")


def write_method_wrapper(gen, cls_name, meth):
    pre_call = PythonCodeGenerator()
    post_call = PythonCodeGenerator()
    docs = []

    passed_args = []
    input_args = []
    doc_args = []
    ret_vals = []
    ret_descrs = []

    arg_idx = 0
    while arg_idx < len(meth.args):
        arg = meth.args[arg_idx]

        if isinstance(arg, CallbackArgument):
            if arg.return_base_type not in SAFE_IN_TYPES or arg.return_ptr:
                raise SignatureNotSupported("non-int callback")

            arg_idx += 1
            if meth.args[arg_idx].name != "user":
                raise SignatureNotSupported("unexpected callback signature")

            cb_wrapper_name = "_cb_wrapper_"+arg.name

            gen_callback_wrapper(pre_call, arg, cb_wrapper_name)

            pre_call(
                '_cb_{name} = ffi.callback("{cb_decl}")({cb_wrapper_name})'
                .format(
                    name=arg.name, cb_decl=arg.c_declarator(),
                    cb_wrapper_name=cb_wrapper_name
                    ))
            input_args.append(arg.name)

            passed_args.append("_cb_"+arg.name)
            passed_args.append("ffi.NULL")

            docs.append(":param %s: callback(%s)"
                    % (arg.name, ", ".join(
                        sub_arg.name
                        for sub_arg in arg.args
                        if sub_arg.name != "user")))

        elif arg.base_type in SAFE_IN_TYPES and not arg.ptr:
            passed_args.append(arg.name)
            input_args.append(arg.name)
            doc_args.append(arg.name)

            pre_call("# no argument processing for {}".format(arg.name))

            doc_cls = arg.base_type
            if doc_cls.startswith("isl_"):
                doc_cls = doc_cls[4:]

            docs.append(":param %s: :class:`%s`" % (arg.name, doc_cls))

        elif arg.base_type in ["char", "const char"] and arg.ptr == "*":
            c_name = "_cstr_"+arg.name

            pre_call('{c_name} = ffi.new("char[]", {arg_name}.encode())'
                    .format(c_name=c_name, arg_name=arg.name))

            if arg.semantics is SEM_TAKE:
                pre_call(
                        "{c_name} = _ManagedCString({c_name})"
                        .format(c_name=c_name))
                passed_args.append(c_name + "._release()")
            else:
                passed_args.append(c_name)
            input_args.append(arg.name)

            docs.append(":param %s: string" % arg.name)

        elif arg.base_type == "int" and arg.ptr == "*":
            if arg.name in ["exact", "tight"]:
                c_name = "cint_"+arg.name
                pre_call('{c_name} = ffi.new("int[1]")'.format(c_name=c_name))

                passed_args.append(c_name)
                ret_vals.append("{c_name}[0]".format(c_name=c_name))
                ret_descrs.append("%s (integer)" % arg.name)
            else:
                raise SignatureNotSupported("int *")

        elif arg.base_type == "isl_val" and arg.ptr == "*" and arg_idx > 0:
            # {{{ val input argument

            val_name = "_val_" + arg.name

            pre_call("""
                if isinstance({name}, Val):
                    {val_name} = {name}._copy()

                elif isinstance({name}, six.integer_types):
                    _cdata_{name} = lib.isl_val_int_from_si(
                        {arg0_name}._get_ctx_data(), {name})

                    if _cdata_{name} == ffi.NULL:
                        raise Error("isl_val_int_from_si failed")

                    {val_name} = _instantiate(Val, _cdata_{name})

                else:
                    raise IslTypeError("{name} is a %s and cannot "
                        "be cast to a Val" % type({name}))
                """
                .format(
                    arg0_name=meth.args[0].name,
                    name=arg.name,
                    val_name=val_name))

            if arg.semantics is SEM_TAKE:
                passed_args.append(val_name + "._release()")
            else:
                passed_args.append(val_name + ".data")
            input_args.append(arg.name)

            docs.append(":param %s: :class:`Val`" % arg.name)

            # }}}

        elif arg.base_type.startswith("isl_") and arg.ptr == "*":
            # {{{ isl types input arguments

            gen_conversions(pre_call, arg.base_type, arg.name)

            arg_py_cls = isl_class_to_py_class(arg.base_type)
            pre_call("if not isinstance({name}, {py_cls}):"
                    .format(
                        name=arg.name, py_cls=arg_py_cls))
            with Indentation(pre_call):
                pre_call('raise IslTypeError("{name} is not a {py_cls}")'
                    .format(
                        name=arg.name, py_cls=arg_py_cls))

            arg_cls = arg.base_type[4:]
            arg_descr = ":param %s: :class:`%s`" % (
                    arg.name, isl_class_to_py_class(arg_cls))

            if arg.semantics is None and arg.base_type != "isl_ctx":
                raise Undocumented(meth)

            copyable = arg_cls not in NON_COPYABLE
            if arg.semantics is SEM_TAKE:
                if copyable:
                    copy_name = "_copy_"+arg.name
                    pre_call('{copy_name} = {name}._copy()'
                            .format(copy_name=copy_name, name=arg.name))

                    passed_args.append(copy_name+"._release()")

                else:
                    if not (arg_idx == 0 and meth.is_mutator):
                        passed_args.append(arg.name+"._release()")
                        arg_descr += " (mutated in-place)"
                    else:
                        passed_args.append(arg.name+".data")
                        arg_descr += " (:ref:`becomes invalid <auto-invalidation>`)"

            elif arg.semantics is SEM_KEEP or arg.semantics is None:
                passed_args.append("%s.data" % arg.name)

            else:
                raise RuntimeError("unexpected semantics: %s" % arg.semantics)

            input_args.append(arg.name)

            docs.append(arg_descr)

            # }}}

        elif arg.base_type.startswith("isl_") and arg.ptr == "**":
            # {{{ isl types output arguments

            if arg.semantics is not SEM_GIVE:
                raise SignatureNotSupported("non-give secondary ptr return value")

            pre_call(
                    '_retptr_{name} = ffi.new("{cls} *")'
                    .format(name=arg.name, cls=arg.base_type))

            passed_args.append("ffi.addressof(_retptr_{name})".format(name=arg.name))

            py_cls = isl_class_to_py_class(arg.base_type)
            post_call("""
                if _retptr_{name} == ffi.NULL:
                    _ret_{name} = None
                else:
                    _ret_{name} = _instantiate({py_cls}, _retptr_{name})
                """
                .format(name=arg.name, cls=arg.base_type, py_cls=py_cls))

            ret_vals.append("_ret_" + arg.name)
            ret_descrs.append("%s (:class:`%s`)" % (arg.name, py_cls))

            # }}}

        elif (arg.base_type == "void"
                and arg.ptr == "*"
                and arg.name == "user"):

            passed_args.append("ffi.NULL")
            input_args.append(arg.name)

            pre_call("""
                if {name} is not None:
                    raise Error("passing non-None arguments for '{name}' "
                        "is not yet supported")
                """
                .format(name=arg.name))

            docs.append(":param %s: None" % arg.name)

        else:
            raise SignatureNotSupported("arg type %s %s" % (arg.base_type, arg.ptr))

        arg_idx += 1
        pre_call("")

    pre_call(
            "_result = lib.{c_name}({args})"
            .format(c_name=meth.c_name, args=", ".join(passed_args)))
    pre_call("")

    # {{{ return value processing

    if meth.return_base_type == "isl_stat" and not meth.return_ptr:
        post_call("if _result == lib.isl_stat_error:")
        with Indentation(post_call):
            post_call('raise Error("call to \\"{}\\" failed")'.format(meth.c_name))

    elif meth.return_base_type == "isl_bool" and not meth.return_ptr:
        post_call("if _result == lib.isl_bool_error:")
        with Indentation(post_call):
            post_call('raise Error("call to \\"{}\\" failed")'.format(meth.c_name))

        ret_vals.insert(0, "_result == lib.isl_bool_true")
        ret_descrs.insert(0, "bool")

    elif meth.return_base_type in SAFE_TYPES and not meth.return_ptr:
        ret_vals.insert(0, "_result")
        ret_descrs.insert(0, meth.return_base_type)

    elif (meth.return_base_type.startswith("isl_")
            and meth.return_semantics is SEM_NULL):
        assert not meth.is_mutator

    elif meth.return_base_type.startswith("isl_"):
        assert meth.return_ptr == "*", meth

        ret_cls = meth.return_base_type[4:]

        if meth.is_mutator:
            if ret_vals:
                meth.mutator_veto = True
                raise Retry()

            post_call("%s._reset(_result)" % meth.args[0].name)

            ret_vals.insert(0, meth.args[0].name)
            ret_descrs.insert(0,
                    ":class:`%s` (self)" % isl_class_to_py_class(ret_cls))
        else:
            if meth.return_semantics is None and ret_cls != "ctx":
                raise Undocumented(meth)

            if meth.return_semantics is not SEM_GIVE and ret_cls != "ctx":
                raise SignatureNotSupported("non-give return")

            post_call("if _result == ffi.NULL:")
            with Indentation(post_call):
                post_call(
                        'raise Error("call to \\"{}\\" failed")'
                        .format(meth.c_name))

            py_ret_cls = isl_class_to_py_class(ret_cls)
            ret_vals.insert(0, "_instantiate({}, _result)".format(py_ret_cls))
            ret_descrs.insert(0,  ":class:`%s`" % py_ret_cls)

    elif meth.return_base_type in ["const char", "char"] and meth.return_ptr == "*":
        post_call("if _result != ffi.NULL:")
        with Indentation(post_call):
            post_call("_str_ret = ffi.string(_result)")
        post_call("else:")
        with Indentation(post_call):
            post_call("_str_ret = None")

        ret_vals.insert(0, "_str_ret")

        if meth.return_semantics is SEM_GIVE:
            post_call("libc.free(_result)")

        ret_descrs.insert(0, "string")

    elif (meth.return_base_type == "void"
            and meth.return_ptr == "*"
            and meth.name == "get_user"):

        raise SignatureNotSupported("get_user")
        # body.append("""
        #     return py::object(py::handle<>(py::borrowed((PyObject *) _result)));
        #     """)
        # ret_descr = "a user-specified python object"

    elif meth.return_base_type == "void" and not meth.return_ptr:
        pass

    else:
        raise SignatureNotSupported("ret type: %s %s in %s" % (
            meth.return_base_type, meth.return_ptr, meth))

    # }}}

    assert len(ret_vals) == len(ret_descrs)

    post_call("")
    if len(ret_vals) == 0:
        ret_descr = "(nothing)"

    elif len(ret_vals) == 1:
        post_call("return " + ret_vals[0])
        ret_descr = ret_descrs[0]

    else:
        post_call("return " + ", ".join(ret_vals))
        ret_descr = "(%s)" % ", ".join(ret_descrs)

    docs = (["%s(%s)" % (meth.name, ", ".join(input_args)), ""]
            + docs
            + [":return: %s" % ret_descr])

    gen("def {name}({input_args}):"
            .format(name=meth.name, input_args=", ".join(input_args)))
    gen.indent()
    gen(repr("\n".join(docs)))
    gen("")
    gen.extend(pre_call)
    gen.extend(post_call)
    gen.dedent()
    gen("")

    method_val = meth.name
    if meth.is_static:
        method_val = "staticmethod(%s)" % method_val

    gen("{py_cls}.{name} = {method_val}"
            .format(
                py_cls=isl_class_to_py_class(meth.cls),
                name=meth.name,
                method_val=method_val))
    gen("")

# }}}


ADD_VERSIONS = {
        "union_pw_aff": 15,
        "multi_union_pw_aff": 15,
        "basic_map_list": 15,
        "map_list": 15,
        "union_set_list": 15,
        }


def gen_wrapper(include_dirs, include_barvinok=False, isl_version=None):
    fdata = FunctionData(["."] + include_dirs)
    fdata.read_header("isl/ctx.h")
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

    if isl_version is None:
        fdata.read_header("isl_declaration_macros_expanded.h")
    else:
        fdata.read_header("isl_declaration_macros_expanded_v%d.h"
                % isl_version)

    if include_barvinok:
        fdata.read_header("barvinok/isl.h")

    undoc = []

    with open("islpy/wrapped-functions.h", "wt") as header_f:
        with open("islpy/_isl.py", "wt") as wrapper_f:
            write_classes_to_header(header_f)
            header_f.write(
                    "// AUTOMATICALLY GENERATED by gen_wrap.py -- do not edit\n\n")
            header_f.write(HEADER_PREAMBLE)

            wrapper_f.write(
                    "# AUTOMATICALLY GENERATED by gen_wrap.py -- do not edit\n")
            wrapper_f.write(PY_PREAMBLE)
            write_classes_to_wrapper(wrapper_f)

            wrapper_gen = PythonCodeGenerator()
            wrapper_gen("# {{{ wrappers")
            wrapper_gen("")
            wrapper_gen("def _add_methods():")

            with Indentation(wrapper_gen):
                for cls_name in CLASSES:
                    if not (
                            isl_version is None
                            or ADD_VERSIONS.get(cls_name) is None
                            or ADD_VERSIONS.get(cls_name) <= isl_version):
                        continue

                    methods = [
                            meth
                            for meth in fdata.classes_to_methods.get(cls_name, [])]

                    wrapper_gen("# {{{ " + cls_name)
                    wrapper_gen("")

                    for meth in methods:
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
                                        % (meth, ", ".join(str(s)
                                            for s in val_versions)))
                                continue

                        write_method_header(header_f, meth)

                        if meth.name == "free":
                            continue

                        try:
                            write_method_wrapper(wrapper_gen, cls_name, meth)
                        except Retry:
                            write_method_wrapper(wrapper_gen, cls_name, meth)
                        except Undocumented:
                            undoc.append(str(meth))
                        except SignatureNotSupported:
                            _, e, _ = sys.exc_info()
                            print("SKIP (sig not supported: %s): %s" % (e, meth))
                        else:
                            #print "WRAPPED:", meth
                            pass

                    wrapper_gen("# }}}")
                    wrapper_gen("")

            wrapper_gen("")
            wrapper_gen("# }}}")
            wrapper_gen("")
            wrapper_gen("_add_methods()")

            wrapper_f.write("\n" + wrapper_gen.get())
            wrapper_f.write("\n\n# vim: fdm=marker\n")

    with open("class_list.py", "wt") as clist_f:
        py_classes = []

        for cls_name in CLASSES:
            py_cls = isl_class_to_py_class(cls_name)
            py_classes.append(py_cls)
            clist_f.write("{py_cls} = _isl.{py_cls}\n".format(py_cls=py_cls))
        clist_f.write("\nALL_CLASSES = [{}]\n".format(", ".join(py_classes)))

    print("SKIP (%d undocumented methods): %s" % (len(undoc), ", ".join(undoc)))

if __name__ == "__main__":
    from os.path import expanduser
    gen_wrapper([expanduser("isl/include")])

# vim: foldmethod=marker
