import argparse
import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from nanobind.stubgen import StubGen as StubGenBase
from typing_extensions import override


class StubGen(StubGenBase):
    # can be removed once https://github.com/wjakob/nanobind/pull/1055 is merged
    @override
    def put_function(self,
                fn: Callable[..., Any],
                name: str | None = None,
                parent: object | None = None
            ):
        fn_module = getattr(fn, "__module__", None)

        if (name and fn_module
                and fn_module != self.module.__name__
                and parent is not None):
            import_name = self.import_object(fn_module, fn.__name__)
            self.write_ln(f"{name} = {import_name}\n")

            return

        super().put_function(fn, name, parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--module", default="islpy._isl")
    parser.add_argument("--exec", nargs="+")
    parser.add_argument("--python-path", nargs="+")
    parser.add_argument("-o", "--output-dir", default="../islpy")
    args = parser.parse_args()
    output_path = Path(cast("str", args.output_dir))

    sys.path.extend(cast("list[str]", args.python_path or []))

    mod = importlib.import_module(cast("str", args.module))
    for fname in cast("list[str]", args.exec or []):
        execdict = {}
        with open(fname) as inf:
            exec(compile(inf.read(), fname, "exec"), execdict)

    sg = StubGen(
        module=mod,
        quiet=True,
        recursive=False,
        include_docstrings=False,
    )
    sg.put(mod)
    prefix_lines = "\n".join([
        "from collections.abc import Callable",
    ])
    with open(output_path / "_isl.pyi", "w") as outf:
        _ = outf.write(f"{prefix_lines}\n{sg.get()}")


if __name__ == "__main__":
    main()
