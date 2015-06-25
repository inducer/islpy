from __future__ import division, with_statement

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

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


# loosely based on
# http://effbot.org/zone/python-code-generator.htm

class Indentation(object):
    def __init__(self, generator):
        self.generator = generator

    def __enter__(self):
        self.generator.indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.generator.dedent()


class PythonCodeGenerator(object):
    def __init__(self):
        self.code = []
        self.level = 0

    def extend(self, sub_generator):
        for line in sub_generator.code:
            self.code.append(" "*(4*self.level) + line)

    def get(self):
        result = "\n".join(self.code)
        return result

    def __call__(self, s):
        if not s.strip():
            self.code.append("")
        else:
            if "\n" in s:
                s = remove_common_indentation(s)

            for l in s.split("\n"):
                self.code.append(" "*(4*self.level) + l)

    def indent(self):
        self.level += 1

    def dedent(self):
        if self.level == 0:
            raise RuntimeError("internal error in python code generator")
        self.level -= 1


# {{{ remove common indentation

def remove_common_indentation(code, require_leading_newline=True):
    if "\n" not in code:
        return code

    # accommodate pyopencl-ish syntax highlighting
    code = code.lstrip("//CL//")

    if require_leading_newline and not code.startswith("\n"):
        return code

    lines = code.split("\n")
    while lines[0].strip() == "":
        lines.pop(0)
    while lines[-1].strip() == "":
        lines.pop(-1)

    if lines:
        base_indent = 0
        while lines[0][base_indent] in " \t":
            base_indent += 1

        for line in lines[1:]:
            if line[:base_indent].strip():
                raise ValueError("inconsistent indentation")

    return "\n".join(line[base_indent:] for line in lines)

# }}}
