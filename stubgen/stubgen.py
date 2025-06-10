import argparse
import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from nanobind.stubgen import StubGen as StubGenBase
from typing_extensions import override


if TYPE_CHECKING:
    import enum


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
            self.import_object(fn_module, name=None)
            rhs = f"{fn_module}.{fn.__qualname__}"
            if type(fn) is staticmethod:
                rhs = f"staticmethod({rhs})"
            self.write_ln(f"{name} = {rhs}\n")

            return

        super().put_function(fn, name, parent)

    @override
    def put(self,
                value: object,
                name: str | None = None,
                parent: object | None = None
            ) -> None:
        if name == "in_" and parent and parent.__name__ == "dim_type":
            # https://github.com/wjakob/nanobind/discussions/1066
            self.write_ln(f"{name} = {cast('enum.Enum', value).value}")

        super().put(value, name, parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--module", default="islpy._isl")
    parser.add_argument("--exec", nargs="+")
    parser.add_argument("--python-path", nargs="+")
    parser.add_argument("-o", "--output-dir", default="../islpy")
    args = parser.parse_args()
    output_path = Path(cast("str", args.output_dir))

    sys.path.extend(cast("list[str]", args.python_path or []))

    os.environ["ISLPY_NO_DOWNCAST_DEPRECATION"] = "1"
    mod = importlib.import_module(cast("str", args.module))
    for fname in cast("list[str]", args.exec or []):
        execdict = {"__name__": "islpy._monkeypatch"}
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
        "from typing_extensions import Self",
        "from collections.abc import Callable",
    ])
    with open(output_path / "_isl.pyi", "w") as outf:
        outf.write(f"{prefix_lines}\n{sg.get()}")


if __name__ == "__main__":
    main()
