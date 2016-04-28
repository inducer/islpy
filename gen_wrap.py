from __future__ import print_function

__copyright__ = "Copyright (C) 2011-15 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

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
    def __init__(self, name, semantics, decl_words, base_type, ptr):
        self.name = name
        self.semantics = semantics
        assert isinstance(decl_words, list)
        self.decl_words = decl_words
        self.base_type = base_type
        self.ptr = ptr

    def c_declarator(self):
        return "{decl_words} {type} {ptr}{name}".format(
                decl_words=" ".join(self.decl_words),
                type=self.base_type,
                ptr=self.ptr,
                name=self.name)


class CallbackArgument:
    def __init__(self, name,
            return_semantics, return_decl_words, return_base_type, return_ptr, args):
        self.name = name
        self.return_semantics = return_semantics
        assert isinstance(return_decl_words, list)
        self.return_decl_words = return_decl_words
        self.return_base_type = return_base_type
        self.return_ptr = return_ptr
        self.args = args

    def c_declarator(self):
        return "{decl_words} {type} {ptr}(*{name})({args})".format(
                decl_words=" ".join(self.return_decl_words),
                type=self.return_base_type,
                ptr=self.return_ptr,
                name=self.name,
                args=", ".join(arg.c_declarator() for arg in self.args))


class Method:
    def __init__(self, cls, name, c_name,
            return_semantics, return_decl_words, return_base_type, return_ptr,
            args, is_exported, is_constructor):
        self.cls = cls
        self.name = name
        self.c_name = c_name
        self.return_semantics = return_semantics
        self.return_decl_words = return_decl_words
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
        # /!\ Order matters, class names that are prefixes of others should go last.

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
        "union_pw_aff_list",
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

        "band", "schedule_constraints", "schedule_node", "schedule",

        "access_info", "flow", "restriction",
        "union_access_info", "union_flow",

        "ast_expr", "ast_node", "ast_print_options",
        "ast_build",
        ]

UNTYPEDEFD_CLASSES = ["options"]


IMPLICIT_CONVERSIONS = {
    "isl_set": [("isl_basic_set", "from_basic_set")],
    "isl_map": [("isl_basic_map", "from_basic_map")],
    "isl_union_set": [("isl_set", "from_set")],
    "isl_union_map": [("isl_map", "from_map")],
    "isl_local_space": [("isl_space", "from_space")],
    "isl_pw_aff": [("isl_aff", "from_aff")],
    }


ENUMS = {
    # ctx.h
    "isl_error": """
        isl_error_none,
        isl_error_abort,
        isl_error_alloc,
        isl_error_unknown,
        isl_error_internal,
        isl_error_invalid,
        isl_error_quota,
        isl_error_unsupported,
    """,
    "isl_stat": """
        isl_stat_error,
        isl_stat_ok,
    """,
    "isl_bool": """
        isl_bool_error,
        isl_bool_false,
        isl_bool_true,
    """,
    # space.h
    "isl_dim_type": """
        isl_dim_cst,
        isl_dim_param,
        isl_dim_in,
        isl_dim_out,
        isl_dim_set,
        isl_dim_div,
        isl_dim_all,
    """,

    # ast_type.h
    "isl_ast_op_type": """
        isl_ast_op_error,
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
        isl_ast_op_fdiv_q,
        isl_ast_op_pdiv_q,
        isl_ast_op_pdiv_r,
        isl_ast_op_zdiv_r,
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
        isl_ast_op_address_of,
    """,
    "isl_ast_expr_type": """
        isl_ast_expr_error,
        isl_ast_expr_op,
        isl_ast_expr_id,
        isl_ast_expr_int,
    """,
    "isl_ast_node_type": """
        isl_ast_node_error,
        isl_ast_node_for,
        isl_ast_node_if,
        isl_ast_node_block,
        isl_ast_node_mark,
        isl_ast_node_user,
    """,
    "isl_ast_loop_type": """
        isl_ast_loop_error,
        isl_ast_loop_default,
        isl_ast_loop_atomic,
        isl_ast_loop_unroll,
        isl_ast_loop_separate,
    """,

    # polynomial_type.h
    "isl_fold": """
        isl_fold_min,
        isl_fold_max,
        isl_fold_list,
    """,

    # printer.h
    "isl_format": """
        ISL_FORMAT_ISL,
        ISL_FORMAT_POLYLIB,
        ISL_FORMAT_POLYLIB_CONSTRAINTS,
        ISL_FORMAT_OMEGA,
        ISL_FORMAT_C,
        ISL_FORMAT_LATEX,
        ISL_FORMAT_EXT_POLYLIB,
    """,

    "isl_yaml_style": """
        ISL_YAML_STYLE_BLOCK,
        ISL_YAML_STYLE_FLOW,
    """,

    # options.h

    "isl_bound": """
        ISL_BOUND_BERNSTEIN,
        ISL_BOUND_RANGE,
    """,

    "isl_on_error": """
        ISL_ON_ERROR_WARN,
        ISL_ON_ERROR_CONTINUE,
        ISL_ON_ERROR_ABORT,
    """,

    "isl_schedule_algorithm": """
        ISL_SCHEDULE_ALGORITHM_ISL,
        ISL_SCHEDULE_ALGORITHM_FEAUTRIER,
    """
    }

TYPEDEFD_ENUMS = ["isl_stat", "isl_bool"]
MACRO_ENUMS = [
        "isl_format", "isl_yaml_style",
        "isl_bound", "isl_on_error", "isl_schedule_algorithm",
        ]

HEADER_PREAMBLE = """
// flow.h
typedef int (*isl_access_level_before)(void *first, void *second);
typedef isl_restriction *(*isl_access_restrict)(
        isl_map *source_map, isl_set *sink,
        void *source_user, void *user);

"""

PY_PREAMBLE = """
from __future__ import print_function

import six
import sys
import logging
import threading


_PY3 = sys.version_info >= (3,)


from islpy._isl_cffi import ffi
lib = ffi.dlopen(None)

from cffi import FFI
libc_ffi = FFI()
libc_ffi.cdef('''
    char *strdup(const char *s);
    void free(void *ptr);
    ''')

libc = libc_ffi.dlopen(None)


class Error(Exception):
    pass


class IslTypeError(Error, TypeError):
    pass

_context_use_map = {}

def _deref_ctx(ctx_data, ctx_iptr):
    _context_use_map[ctx_iptr] -= 1
    if _context_use_map[ctx_iptr] == 0:
        del _context_use_map[ctx_iptr]
        lib.isl_ctx_free(ctx_data)


def _get_last_error_str(ctx_data):
    code = lib.isl_ctx_last_error(ctx_data)
    for name in dir(error):
        if name.startswith("_"):
            continue
        if getattr(error, name) == code:
            return "isl_error_"+name

    return "(unknown error)"


class _ISLObjectBase(object):
    def __init__(self, _data):
        self._setup(_data)

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

    def __eq__(self, other):
        return (type(self) == type(other) and self.data == other.data)

    def __ne__(self, other):
        return not self.__eq__(other)


class _EnumBase(object):
    @classmethod
    def find_value(cls, v):
        for name in dir(cls):
            if getattr(cls, name) == v:
                return name

        raise ValueError("Value '%s' not found in enum" % v)


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


if _PY3:
    class DelayedKeyboardInterrupt(object):
        def __enter__(self):
            self.previous_switch_interval = sys.getswitchinterval()
            sys.setswitchinterval(10000000)

        def __exit__(self, type, value, traceback):
            sys.setswitchinterval(self.previous_switch_interval)
else:
    class DelayedKeyboardInterrupt(object):
        def __enter__(self):
            self.previous_check_interval = sys.getcheckinterval()
            sys.setcheckinterval(100000000)

        def __exit__(self, type, value, traceback):
            sys.setcheckinterval(self.previous_check_interval)

"""

SAFE_TYPES = list(ENUMS) + ["int", "unsigned", "uint32_t", "size_t", "double",
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
    (?:__isl_overload\s*)?
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
STRUCT_DECL_RE = re.compile(
    r"(__isl_export\s+)?"
    "struct\s+"
    "(__isl_subclass\([a-z_ ]+\)\s+)?"
    "([a-z_A-Z0-9]+)\s*;")
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
        return_decl_words = ret_words[:-1]
        return_base_type = ret_words[-1]

        return_ptr = arg_match.group(2)
        name = arg_match.group(3)
        args = [parse_arg(i.strip())
                for i in split_at_unparenthesized_commas(arg_match.group(4))]

        return CallbackArgument(name.strip(),
                return_semantics,
                return_decl_words,
                return_base_type,
                return_ptr.strip(),
                args)

    words = arg.split()
    semantics, words = filter_semantics(words)

    decl_words = []
    if words[0] in ["struct", "enum"]:
        decl_words.append(words.pop(0))

    rebuilt_arg = " ".join(words)
    arg_match = ARG_RE.match(rebuilt_arg)

    base_type = arg_match.group(1).strip()

    if base_type == "isl_args":
        raise BadArg("isl_args not supported")

    assert arg_match is not None, rebuilt_arg
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            decl_words=decl_words,
            base_type=base_type,
            ptr=arg_match.group(2).strip())


class FunctionData:
    def __init__(self, include_dirs):
        self.classes_to_methods = {}
        self.include_dirs = include_dirs
        self.seen_c_names = set()

        self.headers = []

    def read_header(self, fname):
        self.headers.append(fname)

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
                name = name[len(cls)+1:]
                break

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
            if name.startswith("options_"):
                found_class = True
                cls = "ctx"
                name = name[len("options_"):]
            elif name.startswith("equality_") or name.startswith("inequality_"):
                found_class = True
                cls = "constraint"
            elif name == "ast_op_type_set_print_name":
                found_class = True
                cls = "printer"
                name = "ast_op_type_set_print_name"

        if name.startswith("2"):
            name = "two_"+name[1:]

        assert found_class, name

        try:
            args = [parse_arg(arg) for arg in args]
        except BadArg:
            print("SKIP: %s %s" % (cls, name))
            return

        if name in PYTHON_RESERVED_WORDS:
            name = name + "_"

        if cls == "options":
            assert name.startswith("set_") or name.startswith("get_"), (name, c_name)
            name = name[:4]+"option_"+name[4:]

        words = return_base_type.split()

        is_exported = "__isl_export" in words
        if is_exported:
            words.remove("__isl_export")

        is_constructor = "__isl_constructor" in words
        if is_constructor:
            words.remove("__isl_constructor")

        return_semantics, words = filter_semantics(words)
        return_decl_words = []
        if words[0] in ["struct", "enum"]:
            return_decl_words.append(words.pop(0))
        return_base_type = " ".join(words)

        cls_meth_list = self.classes_to_methods.setdefault(cls, [])

        if c_name in self.seen_c_names:
            return

        cls_meth_list.append(Method(
                cls, name, c_name,
                return_semantics, return_decl_words, return_base_type, return_ptr,
                args, is_exported=is_exported, is_constructor=is_constructor))

        self.seen_c_names.add(c_name)

# }}}


# {{{ header writer

def write_enums_to_header(header_f):
    for enum_name, value_str in ENUMS.items():
        values = [v.strip() for v in value_str.split(",") if v.strip()]

        if enum_name not in MACRO_ENUMS:
            if enum_name in TYPEDEFD_ENUMS:
                pattern = "typedef enum {{ {values}, ... }} {name};\n"
            else:
                pattern = "enum {name} {{ {values}, ... }};\n"

            header_f.write(
                    pattern.format(
                        name=enum_name,
                        values=", ".join(values)))
        else:
            for v in values:
                header_f.write("static const int {name};".format(name=v))


def write_classes_to_header(header_f):
    for cls_name in CLASSES:
        header_f.write("struct isl_{name};\n".format(name=cls_name))
        if cls_name not in UNTYPEDEFD_CLASSES:
            header_f.write(
                    "typedef struct isl_{name} isl_{name};\n"
                    .format(name=cls_name))


def write_method_header(header_f, method):
    header_f.write(
            "{return_decl_words} {ret_type} {ret_ptr}{name}({args});\n"
            .format(
                return_decl_words=" ".join(method.return_decl_words),
                ret_type=method.return_base_type,
                ret_ptr=method.return_ptr,
                name=method.c_name,
                args=", ".join(arg.c_declarator() for arg in method.args)))

# }}}


# {{{ python wrapper writer

def write_enums_to_wrapper(wrapper_f):
    gen = PythonCodeGenerator()

    gen("")
    gen("# {{{ enums")
    gen("")
    for enum_name, value_str in ENUMS.items():
        values = [v.strip() for v in value_str.split(",") if v.strip()]

        assert enum_name.startswith("isl_")
        name = enum_name[4:]

        if name == "bool":
            continue

        from os.path import commonprefix
        common_len = len(commonprefix(values))

        gen("class {name}(_EnumBase):".format(name=name))
        with Indentation(gen):
            for val in values:
                py_name = val[common_len:]
                if py_name in PYTHON_RESERVED_WORDS:
                    py_name += "_"
                gen(
                        "{py_name} = lib.{val}"
                        .format(
                            val=val,
                            py_name=py_name,
                            ))

        gen("")

    gen("# }}}")
    gen("")
    wrapper_f.write(gen.get())


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

                        return {py_cls}(_data=data)
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


def gen_callback_wrapper(gen, cb, func_name, has_userptr):
    passed_args = []
    input_args = []

    if has_userptr:
        assert cb.args[-1].name == "user"

    pre_call = PythonCodeGenerator()
    post_call = PythonCodeGenerator()

    for arg in cb.args[:-1]:
        if arg.base_type.startswith("isl_") and arg.ptr == "*":
            input_args.append(arg.name)
            passed_args.append("_py_%s" % arg.name)

            pre_call(
                    "_py_{name} = {py_cls}(_data={name})"
                    .format(
                        name=arg.name,
                        py_cls=isl_class_to_py_class(arg.base_type)))

            if arg.semantics is SEM_TAKE:
                # We (the callback) are supposed to free the object, so
                # just keep it attached to its wrapper until GC gets
                # rid of it.
                pass
            elif arg.semantics is SEM_KEEP:
                # The caller wants to keep this object, so we'll stop managing
                # it.
                post_call("_py_{name}._release()".format(name=arg.name))
            else:
                raise SignatureNotSupported(
                        "callback arg semantics not understood: %s" % arg.semantics)

        else:
            raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                arg.base_type, arg.ptr))

    if has_userptr:
        input_args.append("user")

    if cb.return_base_type in SAFE_IN_TYPES and cb.return_ptr == "":
        failure_return = "lib.isl_stat_error"

        post_call("""
            if _result is None:
                _result = lib.isl_stat_ok
            """)

    elif cb.return_base_type.startswith("isl_") and cb.return_ptr == "*":
        failure_return = "ffi.NULL"

        ret_py_cls = isl_class_to_py_class(cb.return_base_type)

        if cb.return_semantics is None:
            raise SignatureNotSupported("callback return with unspecified semantics")
        elif cb.return_semantics is not SEM_GIVE:
            raise SignatureNotSupported("callback return with non-GIVE semantics")

        post_call("""
            if _result is None:
                _result = ffi.NULL
            elif not isinstance(_result, {py_cls}):
                raise IslTypeError("return value is not a {py_cls}")
            else:
                _result = _result._release()
            """
            .format(py_cls=ret_py_cls))

    else:
        raise SignatureNotSupported("unsupported callback signature")

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

            gen.extend(post_call)

            gen("return _result")

        gen("""
            except Exception as e:
                import sys
                sys.stderr.write("[WARNING] An exception occurred "
                    "in a callback function."
                    "This exception was ignored.\\n")
                sys.stderr.flush()
                import traceback
                traceback.print_exc()

                return {failure_return}
            """.format(failure_return=failure_return))

    gen("")


def write_method_wrapper(gen, cls_name, meth):
    pre_call = PythonCodeGenerator()

    # There are two post-call phases, "safety", and "check". The "safety"
    # phase's job is to package up all the data returned by the function
    # called. No exceptions may be raised before safety ends.
    #
    # Next, the "check" phase will perform error checking and may raise exceptions.
    safety = PythonCodeGenerator()
    check = PythonCodeGenerator()
    docs = []

    passed_args = []
    input_args = []
    doc_args = []
    ret_vals = []
    ret_descrs = []

    def emit_context_check(arg_idx, arg_name):
        if arg_idx == 0:
            pre_call("_ctx_data = {arg_name}._ctx_data".format(arg_name=arg_name))
        else:
            pre_call("""
                if _ctx_data != {arg_name}._ctx_data:
                    raise Error("mismatched context in {arg_name}")
                """.format(arg_name=arg_name))

    arg_idx = 0
    while arg_idx < len(meth.args):
        arg = meth.args[arg_idx]

        if isinstance(arg, CallbackArgument):
            has_userptr = (
                    arg_idx + 1 < len(meth.args)
                    and meth.args[arg_idx+1].name == "user")
            if has_userptr:
                arg_idx += 1

            cb_wrapper_name = "_cb_wrapper_"+arg.name

            gen_callback_wrapper(pre_call, arg, cb_wrapper_name, has_userptr)

            pre_call(
                '_cb_{name} = ffi.callback("{cb_decl}")({cb_wrapper_name})'
                .format(
                    name=arg.name, cb_decl=arg.c_declarator(),
                    cb_wrapper_name=cb_wrapper_name
                    ))

            if (meth.cls in ["ast_build", "ast_print_options"]
                    and meth.name.startswith("set_")):
                # These callbacks need to outlive the set call.
                # Store them on the instance.
                ret_vals.append("_cb_"+arg.name)
                ret_descrs.append(":class:`ffi_callback_handle`")

            input_args.append(arg.name)

            passed_args.append("_cb_"+arg.name)
            if has_userptr:
                passed_args.append("ffi.NULL")

            docs.append(":param %s: callback(%s) -> %s"
                    % (
                        arg.name,
                        ", ".join(
                            sub_arg.name
                            for sub_arg in arg.args
                            if sub_arg.name != "user"),
                        arg.return_base_type
                        ))

        elif arg.base_type in SAFE_IN_TYPES and not arg.ptr:
            passed_args.append(arg.name)
            input_args.append(arg.name)
            doc_args.append(arg.name)

            pre_call("# no argument processing for {0}".format(arg.name))

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
            fmt_args = dict(
                    arg0_name=meth.args[0].name,
                    name=arg.name,
                    val_name=val_name)

            pre_call("if isinstance({name}, Val):".format(**fmt_args))

            with Indentation(pre_call):
                emit_context_check(arg_idx, arg.name)
                pre_call("{val_name} = {name}._copy()".format(**fmt_args))

            pre_call("""
                elif isinstance({name}, six.integer_types):
                    _cdata_{name} = lib.isl_val_int_from_si(
                        {arg0_name}._get_ctx_data(), {name})

                    if _cdata_{name} == ffi.NULL:
                        raise Error("isl_val_int_from_si failed")

                    {val_name} = Val(_data=_cdata_{name})

                else:
                    raise IslTypeError("{name} is a %s and cannot "
                        "be cast to a Val" % type({name}))
                """
                .format(**fmt_args))

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
            pre_call("""
                if not isinstance({name}, {py_cls}):
                    raise IslTypeError("{name} is not a {py_cls}")
                """
                .format(name=arg.name, py_cls=arg_py_cls))

            emit_context_check(arg_idx, arg.name)

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
                    '_retptr_{name} = ffi.new("{cls} **")'
                    .format(name=arg.name, cls=arg.base_type))

            passed_args.append("_retptr_{name}".format(name=arg.name))

            py_cls = isl_class_to_py_class(arg.base_type)
            safety("""
                if _retptr_{name} == ffi.NULL:
                    _ret_{name} = None
                else:
                    _ret_{name} = {py_cls}(_data=_retptr_{name}[0])
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

    # {{{ return value processing

    if meth.return_base_type == "isl_stat" and not meth.return_ptr:
        check("if _result == lib.isl_stat_error:")
        with Indentation(check):
            check('raise Error("call to \\"{0}\\" failed: %s" '
                    '% _get_last_error_str(_ctx_data))'.format(meth.c_name))

    elif meth.return_base_type == "isl_bool" and not meth.return_ptr:
        check("if _result == lib.isl_bool_error:")
        with Indentation(check):
            check('raise Error("call to \\"{0}\\" failed: %s" '
                    '% _get_last_error_str(_ctx_data))'.format(meth.c_name))

        ret_vals.insert(0, "_result == lib.isl_bool_true")
        ret_descrs.insert(0, "bool")

    elif meth.return_base_type in SAFE_TYPES and not meth.return_ptr:
        ret_vals.insert(0, "_result")
        ret_descrs.insert(0, meth.return_base_type)

    elif (meth.return_base_type.startswith("isl_")
            and meth.return_semantics is SEM_NULL):
        assert not meth.is_mutator

    elif meth.return_base_type.startswith("isl_") and meth.return_ptr == "*":
        ret_cls = meth.return_base_type[4:]

        if meth.is_mutator:
            if ret_vals:
                meth.mutator_veto = True
                raise Retry()

            safety("%s._reset(_result)" % meth.args[0].name)

            ret_vals.insert(0, meth.args[0].name)
            ret_descrs.insert(0,
                    ":class:`%s` (self)" % isl_class_to_py_class(ret_cls))
        else:
            if meth.return_semantics is None and ret_cls != "ctx":
                raise Undocumented(meth)

            if meth.return_semantics is not SEM_GIVE and ret_cls != "ctx":
                raise SignatureNotSupported("non-give return")

            py_ret_cls = isl_class_to_py_class(ret_cls)
            safety(
                    "_result = None if "
                    "(_result == ffi.NULL or _result is None) "
                    "else {0}(_data=_result)"
                    .format(py_ret_cls))

            check("""
                if _result is None:
                    raise Error("call to {c_method} failed: %s"
                        % _get_last_error_str(_ctx_data))
                """
                .format(c_method=meth.c_name))

            ret_vals.insert(0, "_result")
            ret_descrs.insert(0,  ":class:`%s`" % py_ret_cls)

    elif meth.return_base_type in ["const char", "char"] and meth.return_ptr == "*":
        safety("""
            if _result != ffi.NULL:
                _str_ret = ffi.string(_result)
            else:
                _str_ret = None
            """)

        if meth.return_semantics is SEM_GIVE:
            safety("libc.free(_result)")

        check("""
            if _PY3 and _str_ret is not None:
                _str_ret = _str_ret.decode()
            """)

        ret_vals.insert(0, "_str_ret")

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

    check("")
    if len(ret_vals) == 0:
        ret_descr = "(nothing)"

    elif len(ret_vals) == 1:
        check("return " + ret_vals[0])
        ret_descr = ret_descrs[0]

    else:
        check("return " + ", ".join(ret_vals))
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
    gen("")

    gen("try:")
    with Indentation(gen):
        gen("_result = None")
        gen("with DelayedKeyboardInterrupt():")
        with Indentation(gen):
            gen(
                "_result = lib.{c_name}({args})"
                .format(c_name=meth.c_name, args=", ".join(passed_args)))

    gen("finally:")
    with Indentation(gen):
        if not (meth.return_base_type == "void" and not meth.return_ptr):
            gen(r"""
                if _result is None:
                    # This should never happen.
                    sys.stderr.write("*** islpy was interrupted while collecting "
                        "a result. "
                        "System state is inconsistent as a result, aborting.\n")
                    sys.stderr.flush()
                    import os
                    os._exit(-1)
                """)

        gen.extend(safety)
        gen("pass")

    gen.extend(check)
    gen.dedent()
    gen("")

    method_val = meth.name
    py_name = meth.name

    if meth.is_static:
        method_val = "staticmethod(%s)" % method_val
    if py_name == "size" and len(meth.args) == 1:
        py_name = "__len__"

    gen("{py_cls}.{py_name} = {method_val}"
            .format(
                py_cls=isl_class_to_py_class(meth.cls),
                py_name=py_name,
                method_val=method_val))
    gen("")

    if meth.is_static:
        gen("{py_cls}._{name}_is_static = True"
                .format(
                    py_cls=isl_class_to_py_class(meth.cls),
                    name=py_name))
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
    fdata.read_header("isl/schedule_node.h")
    fdata.read_header("isl/flow.h")
    fdata.read_header("isl/options.h")
    fdata.read_header("isl/ast.h")
    fdata.read_header("isl/ast_build.h")

    if isl_version is None:
        fdata.read_header("isl_declaration_macros_expanded.h")
    else:
        fdata.read_header("isl_declaration_macros_expanded_v%d.h"
                % isl_version)
    fdata.headers.pop()

    if include_barvinok:
        fdata.read_header("barvinok/isl.h")

    undoc = []

    with open("wrapped-functions.h", "wt") as header_f:
        with open("islpy/_isl.py", "wt") as wrapper_f:
            header_f.write(
                    "// AUTOMATICALLY GENERATED by gen_wrap.py -- do not edit\n\n")
            write_enums_to_header(header_f)
            write_classes_to_header(header_f)
            header_f.write(HEADER_PREAMBLE)

            wrapper_f.write(
                    "# AUTOMATICALLY GENERATED by gen_wrap.py -- do not edit\n")
            wrapper_f.write(PY_PREAMBLE)
            write_enums_to_wrapper(wrapper_f)
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

                        if meth.name in ["free", "set_free_user"]:
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

    with open("name_list.py", "wt") as clist_f:
        py_classes = []

        for cls_name in CLASSES:
            py_cls = isl_class_to_py_class(cls_name)
            py_classes.append(py_cls)
            clist_f.write("{py_cls} = _isl.{py_cls}\n".format(py_cls=py_cls))
        clist_f.write("\n")

        for enum_name in ENUMS:
            py_name = enum_name[4:]

            if py_name == "bool":
                continue

            clist_f.write(
                    "{py_name} = _isl.{py_name}\n"
                    .format(py_name=py_name)
                    )
        clist_f.write("\n")

        clist_f.write("ALL_CLASSES = [{0}]\n".format(", ".join(py_classes)))

    print("SKIP (%d undocumented methods): %s" % (len(undoc), ", ".join(undoc)))

    return fdata.headers

if __name__ == "__main__":
    from os.path import expanduser
    gen_wrapper([expanduser("isl/include")])

# vim: foldmethod=marker
