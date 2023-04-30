import re

from urllib.request import urlopen

_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())

extensions.remove("sphinx.ext.linkcode")

copyright = "2011-21, Andreas Kloeckner"

ver_dic = {}
with open("../islpy/version.py") as vfile:
    exec(compile(vfile.read(), "../islpy/version.py", "exec"), ver_dic)

version = ".".join(str(x) for x in ver_dic["VERSION"])
# The full version, including alpha/beta/rc tags.
release = ver_dic["VERSION_TEXT"]

intersphinx_mapping = {
        "python": ("https://docs.python.org/3/", None),
        }

def autodoc_process_signature(app, what, name, obj, options, signature,
        return_annotation):
    from inspect import ismethod
    if ismethod(obj) and obj.__doc__:
        import re
        pattern = r"^[ \n]*%s(\([a-z_0-9, ]+\))" % re.escape(obj.__name__)
        func_match = re.match(pattern, obj.__doc__)

        if func_match is not None:
            signature = func_match.group(1)
        elif obj.__name__ == "is_valid":
            signature = "()"

    return (signature, return_annotation)

def autodoc_process_docstring(app, what, name, obj, options, lines):
    # clear out redundant pybind-generated member list
    if any("Members" in ln for ln in lines):
        del lines[:]

    arg_list_re = re.compile(r"^([a-zA-Z0-9_]+)\((.*?)\)")

    from inspect import isclass, isroutine
    UNDERSCORE_WHITELIST = ["__len__", "__hash__", "__eq__", "__ne__"]  # noqa: N806
    if isclass(obj) and obj.__name__[0].isupper():
        methods = [nm for nm in dir(obj)
                if isroutine(getattr(obj, nm))
                and (not nm.startswith("_") or nm in UNDERSCORE_WHITELIST)]

        def gen_method_string(meth_name):
            try:
                result = ":meth:`%s`" % meth_name
                meth_obj = getattr(obj, meth_name)
                if meth_obj.__doc__ is None:
                    return result

                doc_match = arg_list_re.match(meth_obj.__doc__)
                if doc_match is None:
                    #print(f"'{meth_obj.__doc__}' did not match arg list RE")
                    return result

                arg_list = doc_match.group(2).split(", ")

                if "self" not in arg_list:
                    result += " (static)"

                return result
            except Exception:
                from traceback import print_exc
                print_exc()
                raise

        if methods:
            lines[:] = [".. hlist::", "  :columns: 2", ""] + [
                    "  * "+gen_method_string(meth_name)
                    for meth_name in methods] + lines

            for nm in methods:
                underscore_autodoc = []
                if nm in UNDERSCORE_WHITELIST:
                    underscore_autodoc.append(".. automethod:: %s" % nm)

                if underscore_autodoc:
                    lines.append("")
                    lines.extend(underscore_autodoc)


def setup(app):
    app.connect("autodoc-process-docstring", autodoc_process_docstring)
    app.connect("autodoc-process-signature", autodoc_process_signature)
