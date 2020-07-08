__copyright__ = "Copyright (C) 2011-20 Andreas Kloeckner"

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
import os
from os.path import join

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


class Retry(RuntimeError):
    pass


class BadArg(ValueError):
    pass


class Undocumented(ValueError):
    pass


class SignatureNotSupported(ValueError):
    pass


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


# {{{ data model

class Argument:
    def __init__(self, name, semantics, base_type, ptr):
        self.name = name
        self.semantics = semantics
        self.base_type = base_type
        self.ptr = ptr


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


class Method:
    def __init__(self, cls, name, c_name,
            return_semantics, return_base_type, return_ptr,
            args, is_exported, is_constructor):
        self.cls = cls
        self.name = name
        assert name
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


# {{{ PART_TO_CLASSES

PART_TO_CLASSES = {
        # If you change this, change:
        # - src/wrapper/wrap_isl.hpp to add WRAP_CLASS(...)
        # - src/wrapper/wrap_isl_partN.hpp to add MAKE_WRAP(...)
        # - doc/reference.rst

        "part1": [
            # lists
            "id_list", "val_list",
            "basic_set_list", "basic_map_list", "set_list", "map_list",
            "union_set_list",
            "constraint_list",
            "aff_list", "pw_aff_list", "pw_multi_aff_list",
            "ast_expr_list", "ast_node_list",
            "pw_qpolynomial_list",
            "pw_qpolynomial_fold_list",
            "union_pw_aff_list",
            "union_pw_multi_aff_list",
            "union_map_list",

            # maps
            "id_to_ast_expr",

            # others
            "ctx",
            "printer",  "val", "multi_val", "vec", "mat", "fixed_box",
            "aff", "pw_aff", "union_pw_aff",
            "multi_aff", "multi_pw_aff", "pw_multi_aff", "union_pw_multi_aff",
            "multi_union_pw_aff",

            "id", "multi_id",

            "constraint", "space", "local_space",
        ],

        "part2": [
            "basic_set", "basic_map",
            "set", "map",
            "union_map", "union_set",
            "point", "vertex", "cell", "vertices",
            "stride_info",
        ],

        "part3": [
            "qpolynomial", "pw_qpolynomial",
            "qpolynomial_fold", "pw_qpolynomial_fold",
            "union_pw_qpolynomial_fold",
            "union_pw_qpolynomial",
            "term",

            "schedule", "schedule_constraints",
            "schedule_node",

            "access_info", "flow", "restriction",
            "union_access_info", "union_flow",

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

# }}}


# {{{ enums

ENUMS = {
    # ctx.h
    "isl_error",
    "isl_stat",
    "isl_bool",

    # space.h
    "isl_dim_type",

    # schedule_type.h
    "isl_schedule_node_type",

    # ast_type.h
    "isl_ast_expr_op_type",
    "isl_ast_expr_type",
    "isl_ast_node_type",
    "isl_ast_loop_type",

    # polynomial_type.h
    "isl_fold",
    }

TYPEDEFD_ENUMS = ["isl_stat", "isl_bool"]
MACRO_ENUMS = [
        "isl_format", "isl_yaml_style",
        "isl_bound", "isl_on_error", "isl_schedule_algorithm",
        ]

# }}}

SAFE_TYPES = list(ENUMS) + ["int", "unsigned", "uint32_t", "size_t", "double",
        "long", "unsigned long", "isl_size"]
SAFE_IN_TYPES = SAFE_TYPES + ["const char *", "char *"]

# {{{ parser helpers

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
STRUCT_DECL_RE = re.compile(r"(__isl_export\s+)?struct\s+([a-z_A-Z0-9]+)\s*;")
ARG_RE = re.compile(r"^((?:\w+)\s+)+(\**)\s*(\w+)$")
INLINE_SEMICOLON_RE = re.compile(r"\;[ \t]*(?=\w)")
SUBCLASS_RE = re.compile(
        r"__isl_subclass\s*"
        r"\(\s*"
        "[0-9a-zA-Z_]+"
        r"\s*\)")


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

    words = [w for w in words if w not in ["struct", "enum"]]

    rebuilt_arg = " ".join(words)
    arg_match = ARG_RE.match(rebuilt_arg)

    assert arg_match is not None, rebuilt_arg
    return Argument(
            name=arg_match.group(3),
            semantics=semantics,
            base_type=arg_match.group(1).strip(),
            ptr=arg_match.group(2).strip())


def preprocess_with_macros(macro_header_contents, code):
    try:
        from pcpp.preprocessor import (
                Preprocessor as PreprocessorBase, OutputDirective, Action)
    except ImportError:
        raise RuntimeError("pcpp was not found. Please install pcpp before "
                "installing islpy. 'pip install pcpp' should do the job.")

    class MacroExpandingCPreprocessor(PreprocessorBase):
        def on_directive_handle(self, directive, toks, ifpassthru, precedingtoks):
            if directive.value == "include":
                raise OutputDirective(action=Action.IgnoreAndPassThrough)
            elif directive.value == "define":
                assert toks
                macro_name = toks[0].value
                if macro_name in ISL_SEM_TO_SEM:
                    raise OutputDirective(action=Action.IgnoreAndRemove)

            return super(MacroExpandingCPreprocessor, self).on_directive_handle(
                    directive, toks, ifpassthru, precedingtoks)

    cpp = MacroExpandingCPreprocessor()
    if sys.version_info < (3,):
        from StringIO import StringIO
    else:
        from io import StringIO

    # read macro definitions, but don't output resulting code
    for macro_header in macro_header_contents:
        cpp.parse(macro_header)
        cpp.write(StringIO())

    sio_output = StringIO()
    cpp.parse(code)
    cpp.write(sio_output)

    return sio_output.getvalue()

# }}}


# {{{ FunctionData (includes parser)

class FunctionData:
    def __init__(self, include_dirs):
        self.classes_to_methods = {}
        self.include_dirs = include_dirs
        self.seen_c_names = set()

    def get_header_contents(self, fname):
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
            return inf.read()
        finally:
            inf.close()

    def get_header_hashes(self, fnames):
        import hashlib
        h = hashlib.sha256()
        h.update(b"v1-")
        for fname in fnames:
            h.update(self.get_header_contents(fname).encode())
        return h.hexdigest()

    preprocessed_dir = "preproc-headers"
    macro_headers = ["isl/multi.h", "isl/list.h"]

    def get_preprocessed_header(self, fname):
        header_hash = self.get_header_hashes(
                self.macro_headers + [fname])

        # cache preprocessed headers to avoid install-time
        # dependency on pcpp
        import errno
        try:
            os.mkdir(self.preprocessed_dir)
        except OSError as err:
            if err.errno == errno.EEXIST:
                pass
            else:
                raise

        prepro_fname = join(self.preprocessed_dir, header_hash)
        try:
            with open(prepro_fname, "rt") as inf:
                return inf.read()
        except OSError:
            pass

        print("preprocessing %s..." % fname)
        macro_header_contents = [
                self.get_header_contents(mh)
                for mh in self.macro_headers]

        prepro_header = preprocess_with_macros(
                macro_header_contents, self.get_header_contents(fname))

        with open(prepro_fname, "wt") as outf:
            outf.write(prepro_header)

        return prepro_header

    # {{{ read_header

    def read_header(self, fname):
        lines = self.get_preprocessed_header(fname).split("\n")

        # heed continuations, split at semicolons
        new_lines = []
        i = 0
        while i < len(lines):
            my_line = lines[i].strip()
            i += 1

            my_line, _ = SUBCLASS_RE.subn("", my_line)
            while my_line.endswith("\\"):
                my_line = my_line[:-1] + lines[i].strip()
                i += 1

            if not my_line.strip().startswith("#"):
                my_line = INLINE_SEMICOLON_RE.sub(";\n", my_line)
                new_lines.extend(my_line.split("\n"))

        lines = new_lines

        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if (not line
                    or line.startswith("extern")
                    or STRUCT_DECL_RE.search(line)
                    or line.startswith("typedef")
                    or line == "}"):
                i += 1
            elif "/*" in line:
                while True:
                    if "*/" in line:
                        i += 1
                        break

                    i += 1

                    line = lines[i].strip()
            elif line.endswith("{"):
                while True:
                    if "}" in line:
                        i += 1
                        break

                    i += 1

                    line = lines[i].strip()

            elif not line:
                i += 1

            else:
                decl = ""

                while True:
                    decl = decl + line
                    if decl:
                        decl += " "
                    i += 1
                    if STRUCT_DECL_RE.search(decl):
                        break

                    open_par_count = sum(1 for i in decl if i == "(")
                    close_par_count = sum(1 for i in decl if i == ")")
                    if open_par_count and open_par_count == close_par_count:
                        break
                    line = lines[i].strip()

                if not STRUCT_DECL_RE.search(decl):
                    self.parse_decl(decl)

    # }}}

    # {{{ parse_decl

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
                "ISL_DECLARE_MULTI_CMP",
                "ISL_DECLARE_MULTI_NEG",
                "ISL_DECLARE_MULTI_DIMS",
                "ISL_DECLARE_MULTI_WITH_DOMAIN",
                "ISL_DECLARE_EXPORTED_LIST_FN",
                "ISL_DECLARE_MULTI_IDENTITY",
                "ISL_DECLARE_MULTI_ARITH",
                "ISL_DECLARE_MULTI_ZERO",
                "ISL_DECLARE_MULTI_NAN",
                "ISL_DECLARE_MULTI_DIM_ID",
                "ISL_DECLARE_MULTI_TUPLE_ID",
                "ISL_DECLARE_MULTI_BIND_DOMAIN",
                "ISL_DECLARE_MULTI_PARAM",
                "ISL_DECLARE_MULTI_DROP_DIMS",
                "isl_malloc_or_die",
                "isl_calloc_or_die",
                "isl_realloc_or_die",
                "isl_handle_error",
                ]:
            return

        assert c_name.startswith("isl_"), c_name
        name = c_name[4:]

        # find longest class name match
        class_name = None
        for it_cls_name in CLASSES:
            if (name.startswith(it_cls_name)
                    and (class_name is None
                        or len(class_name) < len(it_cls_name))):
                class_name = it_cls_name

        # Don't be tempted to chop off "_val"--the "_val" versions of
        # some methods are incompatible with the isl_int ones.
        #
        # (For example, isl_aff_get_constant() returns just the constant,
        # but isl_aff_get_constant_val() returns the constant divided by
        # the denominator.)
        #
        # To avoid breaking user code in non-obvious ways, the new
        # names are carried over to the Python level.

        if class_name is not None:
            name = name[len(class_name)+1:]
        else:
            if name.startswith("bool_"):
                return
            if name.startswith("options_"):
                class_name = "ctx"
                name = name[len("options_"):]
            elif name.startswith("equality_") or name.startswith("inequality_"):
                class_name = "constraint"
            elif name == "ast_op_type_set_print_name":
                class_name = "printer"
                name = "ast_op_type_set_print_name"

        assert class_name is not None

        if name in ["free", "cow"]:
            return

        try:
            args = [parse_arg(arg) for arg in args]
        except BadArg:
            print("SKIP: %s %s" % (class_name, name))
            return

        if name in PYTHON_RESERVED_WORDS:
            name = name + "_"

        if class_name == "options":
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
        words = [w for w in words if w not in ["struct", "enum"]]
        return_base_type = " ".join(words)

        cls_meth_list = self.classes_to_methods.setdefault(class_name, [])

        if c_name in self.seen_c_names:
            return

        cls_meth_list.append(Method(
                class_name, name, c_name,
                return_semantics, return_base_type, return_ptr,
                args, is_exported=is_exported, is_constructor=is_constructor))

        self.seen_c_names.add(c_name)

    # }}}

# }}}


# {{{ get_callback

def get_callback(cb_name, cb):
    pre_call = []
    passed_args = []
    post_call = []

    assert cb.args[-1].name == "user"

    for arg in cb.args[:-1]:
        if arg.base_type.startswith("isl_"):
            if arg.ptr != "*":
                raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                    arg.base_type, arg.ptr))
            arg_cls = arg.base_type[4:]

            passed_args.append("arg_%s" % arg.name)

            pre_call.append("""
                %(arg_cls)s *wrapped_arg_%(name)s(new %(arg_cls)s(c_arg_%(name)s));
                py::object arg_%(name)s(
                    handle_from_new_ptr(wrapped_arg_%(name)s));
                """ % dict(
                    arg_cls=arg_cls,
                    name=arg.name,
                    ))

            if arg.semantics is SEM_TAKE:
                # We (the callback) are supposed to free the object, so
                # just let the unique_ptr get rid of it.
                pass
            elif arg.semantics is SEM_KEEP:
                # The caller wants to keep this object, so we simply tell our
                # wrapper to stop managing it after the call completes.
                post_call.append("""
                    wrapped_arg_%(name)s->invalidate();
                    """ % {"name": arg.name})
            else:
                raise SignatureNotSupported("unsupported callback arg semantics")

        else:
            raise SignatureNotSupported("unsupported callback arg: %s %s" % (
                arg.base_type, arg.ptr))

    if cb.return_base_type in SAFE_IN_TYPES and not cb.return_ptr:
        ret_type = "%s %s" % (cb.return_base_type, cb.return_ptr)
        if cb.return_base_type == "isl_stat":
            post_call.append("""
                if (retval.ptr() == Py_None)
                {
                    return isl_stat_ok;
                }
                """)
        else:
            post_call.append("""
                if (retval.ptr() == Py_None)
                {
                    throw isl::error("callback returned None");
                }
                """)
        post_call.append("""
                else
                    return py::cast<%(ret_type)s>(retval);
            """ % {
                "ret_type": ret_type,
                }
            )
        if cb.return_base_type == "isl_bool":
            error_return = "isl_bool_error"
        else:
            error_return = "isl_stat_error"

    elif cb.return_base_type.startswith("isl_") and cb.return_ptr == "*":
        if cb.return_semantics is None:
            raise SignatureNotSupported("callback return with unspecified semantics")
        elif cb.return_semantics is not SEM_GIVE:
            raise SignatureNotSupported("callback return with non-GIVE semantics")

        ret_type = "%s %s" % (cb.return_base_type, cb.return_ptr)
        post_call.append("""
            if (retval.ptr() == Py_None)
            {
                return nullptr;
            }
            else
            {
                isl::%(ret_type_name)s *wrapper_retval =
                    py::cast<isl::%(ret_type_name)s *>(retval);
                isl_%(ret_type_name)s *unwrapped_retval =
                    wrapper_retval->m_data;
                wrapper_retval->invalidate();
                return unwrapped_retval;
            }
            """ % {
                "ret_type_name": cb.return_base_type[4:],
                }
            )
        error_return = "nullptr"

    else:
        raise SignatureNotSupported("non-int callback")

    return """
        static %(ret_type)s %(cb_name)s(%(input_args)s)
        {
            py::object py_cb = py::reinterpret_borrow<py::object>(
                (PyObject *) c_arg_user);
            try
            {
              %(pre_call)s
              py::object retval = py_cb(%(passed_args)s);
              %(post_call)s
            }
            catch (py::error_already_set &err)
            {
              std::cout << "[islpy warning] A Python exception occurred in "
                "a call back function, ignoring:" << std::endl;
              PyErr_Print();
              return %(error_return)s;
            }
            catch (std::exception &e)
            {
              std::cerr << "[islpy] An exception occurred in "
                "a Python callback query:" << std::endl
                << e.what() << std::endl;
              std::cout << "[islpy] Aborting now." << std::endl;
              return %(error_return)s;
            }
        }
        """ % dict(
                ret_type=ret_type,
                cb_name=cb_name,
                input_args=(
                    ", ".join("%s %sc_arg_%s" % (arg.base_type, arg.ptr, arg.name)
                        for arg in cb.args)),
                pre_call="\n".join(pre_call),
                passed_args=", ".join(passed_args),
                post_call="\n".join(post_call),
                error_return=error_return,
                )

# }}}


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
            has_userptr = (
                    arg_idx + 1 < len(meth.args)
                    and meth.args[arg_idx+1].name.endswith("user"))
            if not has_userptr:
                raise SignatureNotSupported(
                        "callback signature without user pointer")
            else:
                arg_idx += 1

            if meth.args[arg_idx].name != "user":
                raise SignatureNotSupported("unexpected callback signature")

            cb_name = "cb_%s_%s_%s" % (meth.cls, meth.name, arg.name)

            if (meth.cls in ["ast_build", "ast_print_options"]
                    and meth.name.startswith("set_")):
                extra_ret_vals.append("py_%s" % arg.name)
                extra_ret_descrs.append("(opaque handle to "
                        "manage callback lifetime)")

            input_args.append("py::object py_%s" % arg.name)
            passed_args.append(cb_name)
            passed_args.append("py_%s.ptr()" % arg.name)

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

        elif arg.base_type in ["int", "isl_bool"] and arg.ptr == "*":
            if arg.name in ["exact", "tight"]:
                body.append("%s arg_%s;" % (arg.base_type, arg.name))
                passed_args.append("&arg_%s" % arg.name)
                if arg.base_type == "isl_bool":
                    extra_ret_vals.append("(bool) arg_%s" % arg.name)
                else:
                    extra_ret_vals.append("arg_%s" % arg.name)
                extra_ret_descrs.append("%s (%s)" % (
                    arg.name, to_py_class(arg.base_type)))
                arg_names.pop()
            else:
                raise SignatureNotSupported("int *")

        elif arg.base_type == "isl_val" and arg.ptr == "*" and arg_idx > 0:
            # {{{ val input argument

            arg_descr = ":param %s: :class:`Val`" % arg.name
            input_args.append("py::object py_%s" % arg.name)
            checks.append("""
                std::unique_ptr<val> unique_arg_%(name)s;
                isl_ctx *ctx_for_%(name)s =
                    %(first_arg_base_type)s_get_ctx(arg_%(first_arg)s.m_data);

                try
                {
                    val *arg_%(name)s = py::cast<val *>(py_%(name)s);
                    isl_val *tmp_ptr = isl_val_copy(arg_%(name)s->m_data);
                    if (!tmp_ptr)
                        throw isl::error("failed to copy arg %(name)s");
                    unique_arg_%(name)s = std::unique_ptr<val>(new val(tmp_ptr));
                }
                catch (py::cast_error &err)
                {
                    // fall through to next case
                }

                try
                {
                    if (!unique_arg_%(name)s.get())
                    {
                        isl_val *tmp_ptr = isl_val_int_from_si(ctx_for_%(name)s,
                          py::cast<long>(py_%(name)s));
                        if (!tmp_ptr)
                            throw isl::error("failed to create arg "
                                "%(name)s from integer");
                        unique_arg_%(name)s = std::unique_ptr<val>(new val(tmp_ptr));
                    }
                }
                catch (py::cast_error &err)
                {
                    throw isl::error("unrecognized argument for %(name)s");
                }
                """ % dict(
                    name=arg.name,
                    first_arg_base_type=meth.args[0].base_type,
                    first_arg=meth.args[0].name,
                    ))

            if arg.semantics is None and arg.base_type != "isl_ctx":
                raise Undocumented(meth)

            if arg.semantics is SEM_TAKE:
                post_call.append("unique_arg_%s.release();" % arg.name)

            passed_args.append("unique_arg_%s->m_data" % arg.name)
            docs.append(arg_descr)

            # }}}

        elif arg.base_type.startswith("isl_") and arg.ptr == "*":
            # {{{ isl types input arguments

            arg_cls = arg.base_type[4:]
            arg_descr = ":param %s: :class:`%s`" % (arg.name, to_py_class(arg_cls))

            if arg_idx == 0 and meth.is_mutator:
                arg_descr += " (mutated in-place)"
                input_args.append("py::object py_%s" % arg.name)
                checks.append("""
                    isl::%(cls)s &arg_%(name)s(
                        py::cast<isl::%(cls)s &>(py_%(name)s));
                    if (!arg_%(name)s.is_valid())
                      throw isl::error(
                        "passed invalid arg to isl_%(meth)s for %(name)s");
                    """ % dict(
                        name=arg.name,
                        meth="%s_%s" % (meth.cls, meth.name),
                        cls=arg_cls))
                passed_args.append("arg_%s.m_data" % arg.name)
                post_call.append("arg_%s.invalidate();" % arg.name)
                arg_descr += " (mutated in-place)"

            else:
                if arg.semantics is None and arg.base_type != "isl_ctx":
                    raise Undocumented(meth)

                checks.append("""
                    if (!arg_%(name)s.is_valid())
                      throw isl::error(
                        "passed invalid arg to isl_%(meth)s for %(name)s");
                    """ % dict(name=arg.name, meth="%s_%s" % (meth.cls, meth.name)))

                if arg.semantics is SEM_TAKE:
                    if arg_cls not in NON_COPYABLE:
                        input_args.append(
                                "%s const &%s" % (arg_cls, "arg_"+arg.name))
                        checks.append("""
                            std::unique_ptr<%(cls)s> auto_arg_%(name)s;
                            {
                                isl_%(cls)s *tmp_ptr =
                                    isl_%(cls)s_copy(arg_%(name)s.m_data);
                                if (!tmp_ptr)
                                    throw isl::error("failed to copy arg "
                                        "%(name)s on entry to %(meth)s");
                                auto_arg_%(name)s = std::unique_ptr<%(cls)s>(
                                    new %(cls)s(tmp_ptr));
                            }
                            """ % dict(
                                name=arg.name,
                                meth="%s_%s" % (meth.cls, meth.name),
                                cls=arg_cls))

                        post_call.append("auto_arg_%s.release();" % arg.name)
                        passed_args.append("auto_arg_%s->m_data" % arg.name)

                    else:
                        input_args.append("%s &%s" % (arg_cls, "arg_"+arg.name))
                        post_call.append("arg_%s.invalidate();" % arg.name)
                        passed_args.append("arg_%s.m_data" % arg.name)
                        arg_descr += " (:ref:`becomes invalid <auto-invalidation>`)"
                else:
                    passed_args.append("arg_%s.m_data" % arg.name)
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
                  py_ret_%(name)s = handle_from_new_ptr(
                      new %(ret_cls)s(ret_%(name)s));
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
        # {{{ integer return

        if meth.name.startswith("is_") or meth.name.startswith("has_"):
            processed_return_type = "bool"

        ret_descr = processed_return_type

        if extra_ret_vals:
            if len(extra_ret_vals) == 1:
                processed_return_type = "py::object"
                body.append("return py::object(result, %s);" % extra_ret_vals[0])
                ret_descr = extra_ret_descrs[0]
            else:
                processed_return_type = "py::object"
                body.append("return py::make_tuple(result, %s);"
                        % ", ".join(extra_ret_vals))
                ret_descr = "tuple: (%s)" % (", ".join(extra_ret_descrs))
        else:
            body.append("return result;")

        # }}}

    elif meth.return_base_type == "isl_stat" and not meth.return_ptr:
        # {{{ error code

        body.append("""
            if (result == isl_stat_error)
            {
              throw isl::error("call to isl_%(cls)s_%(name)s failed");
            }""" % {"cls": meth.cls, "name": meth.name})

        assert not (meth.name.startswith("is_") or meth.name.startswith("has_"))

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

        # }}}

    elif meth.return_base_type == "isl_bool" and not meth.return_ptr:
        # {{{ bool

        body.append("""
            if (result == isl_bool_error)
            {
              throw isl::error("call to isl_%(cls)s_%(name)s failed");
            }""" % {"cls": meth.cls, "name": meth.name})

        processed_return_type = "bool"
        ret_descr = "bool"

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

        # }}}

    elif meth.return_base_type in SAFE_TYPES and not meth.return_ptr:
        # {{{ enums etc

        if extra_ret_vals:
            raise NotImplementedError("extra ret val with safe type")

        body.append("return result;")
        ret_descr = processed_return_type

        # }}}

    elif meth.return_base_type.startswith("isl_"):
        assert meth.return_ptr == "*", meth

        ret_cls = meth.return_base_type[4:]

        if meth.is_mutator:
            if extra_ret_vals:
                meth.mutator_veto = True
                raise Retry()

            processed_return_type = "py::object"
            body.append("arg_%s.take_possession_of(result);" % meth.args[0].name)
            body.append("return py_%s;" % meth.args[0].name)

            ret_descr = ":class:`%s` (self)" % to_py_class(ret_cls)
        else:
            processed_return_type = "py::object"
            isl_obj_ret_val = \
                    "handle_from_new_ptr(uptr_result.release())"

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
                    std::unique_ptr <isl::%(ret_cls)s>
                        uptr_result(new %(ret_cls)s(result));
                    return %(ret_val)s;
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
              return py::cast(std::string(result));
            else
              return py::none();
            """)
        if meth.return_semantics is SEM_GIVE:
            body.append("free(result);")

        ret_descr = "string"

    elif (meth.return_base_type == "void"
            and meth.return_ptr == "*"
            and meth.name == "get_user"):

        body.append("""
            return py::reinterpret_borrow<py::object>((PyObject *) result);
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

def write_exposer(outf, meth, arg_names, doc_str):
    func_name = "isl::%s_%s" % (meth.cls, meth.name)
    py_name = meth.name

    nonself_arg_names = arg_names
    if not meth.is_static:
        nonself_arg_names = nonself_arg_names[1:]
    args_str = ", ".join('py::arg("%s")' % arg_name
            for arg_name in nonself_arg_names)
    if args_str:
        args_str = ", %s" % args_str

    if meth.name == "size" and len(meth.args) == 1:
        py_name = "__len__"

    if meth.name == "get_hash" and len(meth.args) == 1:
        py_name = "__hash__"

    extra_py_names = []

    #if meth.is_static:
    #    doc_str = "(static method)\n" + doc_str

    doc_str_arg = ", \"%s\"" % doc_str.replace("\n", "\\n")

    wrap_class = CLASS_MAP.get(meth.cls, meth.cls)

    for exp_py_name in [py_name]+extra_py_names:
        outf.write("wrap_%s.def%s(\"%s\", %s%s);\n" % (
            wrap_class, "_static" if meth.is_static else "",
            exp_py_name, func_name, args_str+doc_str_arg))

# }}}


def write_wrappers(expf, wrapf, methods):
    undoc = []

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
            write_exposer(expf, meth, arg_names, doc_str)
        except Undocumented:
            undoc.append(str(meth))
        except Retry:
            arg_names, doc_str = write_wrapper(wrapf, meth)
            write_exposer(expf, meth, arg_names, doc_str)
        except SignatureNotSupported:
            _, e, _ = sys.exc_info()
            print("SKIP (sig not supported: %s): %s" % (e, meth))
        else:
            #print "WRAPPED:", meth
            pass

    print("SKIP (%d undocumented methods): %s" % (len(undoc), ", ".join(undoc)))


ADD_VERSIONS = {
        "union_pw_aff": 15,
        "multi_union_pw_aff": 15,
        "basic_map_list": 15,
        "map_list": 15,
        "union_set_list": 15,
        }


def gen_wrapper(include_dirs, include_barvinok=False, isl_version=None):
    fdata = FunctionData(["."] + include_dirs)
    fdata.read_header("isl/id.h")
    fdata.read_header("isl/space.h")
    fdata.read_header("isl/set.h")
    fdata.read_header("isl/map.h")
    fdata.read_header("isl/map_type.h")
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
    fdata.read_header("isl/schedule.h")
    fdata.read_header("isl/schedule_node.h")
    fdata.read_header("isl/flow.h")
    fdata.read_header("isl/options.h")
    fdata.read_header("isl/ast.h")
    fdata.read_header("isl/ast_build.h")
    fdata.read_header("isl/ast_type.h")
    fdata.read_header("isl/ilp.h")

    if include_barvinok:
        fdata.read_header("barvinok/isl.h")

    for part, classes in PART_TO_CLASSES.items():
        expf = open("src/wrapper/gen-expose-%s.inc" % part, "wt")
        wrapf = open("src/wrapper/gen-wrap-%s.inc" % part, "wt")

        classes = [
                cls
                for cls in classes
                if isl_version is None
                or ADD_VERSIONS.get(cls) is None
                or ADD_VERSIONS.get(cls) <= isl_version]

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
