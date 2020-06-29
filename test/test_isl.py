# encoding: utf-8
from __future__ import division, print_function

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

import islpy as isl
import pytest  # noqa


def test_basics():
    dt = isl.dim_type

    ctx = isl.Context()
    space = isl.Space.create_from_names(ctx, set=["a", "b"])

    bset = (isl.BasicSet.universe(space)
            .add_constraint(isl.Constraint.eq_from_names(
                space, {"a": -1, "b": 2}))
            .add_constraint(isl.Constraint.ineq_from_names(
                space, {"a": 1, 1: -10}))
            .add_constraint(isl.Constraint.ineq_from_names(
                space, {"a": -1, 1: 42}))
            .project_out(dt.set, 1, 1))

    bset2 = isl.BasicSet(  # noqa
            "{[i] : exists (a : i = 2a and i >= 10 and i <= 42)}",
            context=ctx)

    points = []
    bset.foreach_point(points.append)

    for pt in points:
        print(pt)


def test_error_on_invalid_index():
    ctx = isl.Context()
    my_set = isl.Set("{ [k, l] : 3l >= -k and 3l <= 10 - k "
                   "and k >=0 and k <= 2 }", context=ctx)
    p = my_set.sample_point()
    with pytest.raises(isl.Error):
        p.get_coordinate_val(isl.dim_type.set, 99999999)


def test_pwqpoly():
    def term_handler(term):
        print(term.get_coefficient_val())

    def piece_handler(set, qpoly):
        qpoly.foreach_term(term_handler)

    pwqp = isl.PwQPolynomial('[n] -> { n }')
    pwqp.foreach_piece(piece_handler)


def no_test_id_user():
    ctx = isl.Context()
    foo = isl.Id("foo", context=ctx)  # noqa
    t = (1, 2)
    bar = isl.Id("bar", t, context=ctx)

    assert bar.user is t


def test_val():
    for src in [17, "17"]:
        v = isl.Val(src)
        print(v)
        assert v == 17
        assert v.to_python() == 17


def test_upcast():
    a = isl.PwAff("[n] -> { [(-1 - floor((-n)/4))] }")
    b = isl.Aff("[n] -> { [(-1 - floor((-n)/4))] }")

    assert b.is_equal(a)
    assert a.is_equal(b)


def test_pickling():
    instances = [
            isl.Aff("[n] -> { [(-1 - floor((-n)/4))] }"),
            isl.PwAff("[n] -> { [(0)] : n <= 4 and n >= 1; "
                "[(-1 + n - floor((3n)/4))] : n >= 5 }"),
            isl.BasicSet("[n] -> {[i,j,k]: i<=j + k and (exists m: m=j+k) "
                "and n mod 5 = 17}"),
            isl.Set("[n] -> {[i,j,k]: (i<=j + k and (exists m: m=j+k)) or (k=j)}")
            ]

    from pickle import dumps, loads
    for inst in instances:
        inst2 = loads(dumps(inst))

        assert inst.space == inst2.space
        assert inst.is_equal(inst2)


def test_get_id_dict():
    print(isl.Set("[a] -> {[b]}").get_id_dict(isl.dim_type.param))


def test_get_coefficients_by_name():
    my_set = isl.BasicSet("{ [k, l] : 3l >= -k and 3l <= 10 - k "
                   "and k >=0 and k <= 2 }")

    for c in my_set.get_constraints():
        print(c.get_coefficients_by_name())


def test_count_brick_ish():
    a = isl.BasicSet("[n] -> {[i,j]: 0<= i < n and 0<= j < n and j<= i}")

    def count(bset):
        result = 1

        for i in range(bset.dim(isl.dim_type.set)):
            dmax = bset.dim_max(i)
            dmin = bset.dim_min(i)

            length = isl.PwQPolynomial.from_pw_aff(dmax - dmin + 1)

            result = result * length

        return result

    counts = [count(a)]

    if hasattr(a, "card"):
        counts.append(a.card())

    for pwq in counts:
        print("EVAL", pwq, "=", pwq.eval_with_dict(dict(n=10)))


def test_eval_pw_qpolynomial():
    pwaff = isl.PwAff("[n] -> { [(0)] : n <= 4 and n >= 1; "
        "[(-1 + n - floor((3n)/4))] : n >= 5 }")

    pwq = isl.PwQPolynomial.from_pw_aff(pwaff)

    pwq.eval_with_dict(dict(n=10))


def test_schedule():
    schedule = isl.Map("{S[t,i,j] -> [t,i,j]: 0 < t < 20 and 0 < i < j < 100}")
    accesses = isl.Map("{S[t,i,j] -> bar[t%2, i+1, j-1]}")
    context = isl.Set("{:}")
    build = isl.AstBuild.from_context(context)

    def callback(node, build):
        schedulemap = build.get_schedule()
        accessmap = accesses.apply_domain(schedulemap)
        aff = isl.PwMultiAff.from_map(isl.Map.from_union_map(accessmap))
        access = build.call_from_pw_multi_aff(aff)
        return isl.AstNode.alloc_user(access)

    build, callback_handle = build.set_at_each_domain(callback)

    ast = build.ast_from_schedule(schedule)

    def cb_print_user(printer, options, node):
        print("Callback user called")
        printer = printer.print_str("Callback user")
        return printer

    def cb_print_for(printer, options, node):
        print("Callback for called")
        printer = printer.print_str("Callback For")
        return printer

    opts = isl.AstPrintOptions.alloc(isl.DEFAULT_CONTEXT)
    opts, cb_print_user_handle = opts.set_print_user(cb_print_user)
    opts, cb_print_for_handle = opts.set_print_for(cb_print_for)

    printer = isl.Printer.to_str(isl.DEFAULT_CONTEXT)
    printer = printer.set_output_format(isl.format.C)
    printer.print_str("// Start\n")
    printer = ast.print_(printer, opts)
    printer.print_str("// End")

    print(printer.get_str())


def test_union_map():
    d = isl.UnionSet("[start, num] -> {S[i,j] : start <= i,j < start + num}")
    s = isl.UnionMap("{S[i,j] -> [i,j]}").intersect_domain(d)
    aw = isl.UnionMap("{S[i,j] -> B[1024 i + j]}")
    aw.compute_flow(aw, aw, s)


def test_schedule_dump():
    ctx = isl.Context()
    s = isl.UnionSet.read_from_str(ctx,
            "{ S_2[i, j, k] : i <= 99 and i >= 0; S_3[i] : "
            "i <= 99 and i >= 0; S_0[]; S_1[i] : i <= 99 and i >= 0 }")
    cst = isl.ScheduleConstraints.on_domain(s)
    schedule = isl.ScheduleConstraints.compute_schedule(cst)
    schedule.dump()


def test_from_union_map():
    ctx = isl.Context()
    m = isl.UnionMap.read_from_str(ctx,
        "[m, n] -> { S_0[] -> [0, 0, 0, 0]; S_1[i] -> [i, 1, 0, 0]; S_3[i] -> "
        "[1 + i, 3, 0, 0]; S_2[i, j, k] -> [i, 2, j, k] : "
        "j <= -1 + m and j >= 0 and k <= -1 + n and k >= 0 }")

    isl.MultiUnionPwAff.from_union_map(m)


def test_get_schedule_map():
    ctx = isl.Context()
    ss = isl.UnionSet.read_from_str(
        ctx, "[m, n] -> { S_2[i, j, k] : "
        "j <= -1 + m and j >= 0 and k <= -1 + n and k >= 0 }")
    cst1 = isl.ScheduleConstraints.on_domain(ss)
    sub_schedule = isl.ScheduleConstraints.compute_schedule(cst1)
    sub_schedule.get_map()


def test_codegen():
    # courtesy of Marek Pałkowski

    def isl_ast_codegen(S):  # noqa: N803
        b = isl.AstBuild.from_context(isl.Set("{:}"))
        m = isl.Map.from_domain_and_range(S, S)
        m = isl.Map.identity(m.get_space())
        m = isl.Map.from_domain(S)
        ast = b.ast_from_schedule(m)
        p = isl.Printer.to_str(isl.DEFAULT_CONTEXT)
        p = p.set_output_format(isl.format.C)
        p.flush()
        p = p.print_ast_node(ast)
        return p.get_str()

    s = isl.Set("[n,m] -> { [i,j] : 0 <= i <= n and i <= j <= m }")
    print(isl_ast_codegen(s))


def test_make_zero_and_vars():
    v = isl.make_zero_and_vars("i,j,k", "n")

    myset = (
            v[0].le_set(v["i"] + v["j"])
            & (v["i"] + v["j"]).lt_set(v["n"])
            & (v[0].le_set(v["i"]))
            & (v["i"].le_set(13 + v["n"]))
            )

    print(myset)


def test_affs_from_space():
    s = isl.Set("[n] -> {[i,j,k]: 0<=i,j,k<n}")
    v = isl.affs_from_space(s.space)

    myset = (
            v[0].le_set(v["i"] + v["j"])
            & (v["i"] + v["j"]).lt_set(v["n"])
            & (v[0].le_set(v["i"]))
            & (v["i"].le_set(13 + v["n"]))
            )

    print(myset)


def test_id_constructor():
    ctx = isl.Context()
    isl.Id(context=ctx, name='x0')


def test_creation_error():
    # note the (intentional) syntax error
    with pytest.raises(isl.Error):
        isl.BasicSet(
                "[n0, n1] -> "
                "{ [i0, i1, i2] : 0 <= i0 < n1  and 0 and 0 <= i2 <= 15 }")


def test_lexmin():
    print(isl.Set("""{ [s] : exists a,b,c :
            0 <= a <= 5 and 1 <= b <= 4 and 2 <= c <= 7 and
            ((2 <= b and b <= 3) implies (a <= 1 or a >= 3)) and
            ((not (c < 5 or b > 3)) implies (a > 2 and c < 3)) and s = a + b + c }
            """).lexmin())


def test_align_spaces():
    m1 = isl.BasicMap("[m,n] -> {[i,j,k]->[l,o]:}")
    m2 = isl.BasicMap("[m,n] -> {[j,k,l,i]->[o]:}")

    result = isl.align_spaces(m1, m2)
    assert result.get_var_dict() == m2.get_var_dict()

    a1 = isl.Aff("[t0, t1, t2] -> { [(32)] }")
    a2 = isl.Aff("[t1, t0] -> { [(0)] }")

    with pytest.raises(isl.Error):
        a1_aligned = isl.align_spaces(a1, a2)

    a1_aligned = isl.align_spaces(a1, a2, obj_bigger_ok=True)
    a2_aligned = isl.align_spaces(a2, a1)

    assert a1_aligned == isl.Aff("[t1, t0, t2] -> { [(32)] }")
    assert a2_aligned == isl.Aff("[t1, t0, t2] -> { [(0)] }")


def test_pass_numpy_int():
    np = pytest.importorskip("numpy")

    s = isl.BasicMap("{[i,j]: 0<=i,j<15}")
    c0 = s.get_constraints()[0]

    c1 = c0.set_constant_val(np.int32(5))
    print(c1)


def test_isl_align_two():
    a1 = isl.Aff("[t0, t1, t2] -> { [(32)] }")
    a2 = isl.Aff("[t1, t0] -> { [(0)] }")

    a1_aligned, a2_aligned = isl.align_two(a1, a2)
    assert a1_aligned == isl.Aff("[t1, t0, t2] -> { [(32)] }")
    assert a2_aligned == isl.Aff("[t1, t0, t2] -> { [(0)] }")

    b1 = isl.BasicSet("[n0, n1, n2] -> { [i0, i1] : }")
    b2 = isl.BasicSet("[n0, n2, n1, n3] -> { [i1, i0, i2] : }")

    b1_aligned, b2_aligned = isl.align_two(b1, b2)
    assert b1_aligned == isl.BasicSet("[n0, n2, n1, n3] -> { [i1, i0, i2] :  }")
    assert b2_aligned == isl.BasicSet("[n0, n2, n1, n3] -> { [i1, i0, i2] :  }")


def test_bound():
    print(isl.PwQPolynomial("""[n, m] -> {[i, j] -> i * m + j :
            0 <= i < n and 0 <= j < m}""").bound(isl.fold.min))
    print(isl.PwQPolynomial("""[n, m] -> {[i, j] -> i * m + j :
            0 <= i < n and 0 <= j < m}""").bound(isl.fold.max))


def test_copy_context():
    ctx = isl.Context()
    import copy
    assert not ctx._wraps_same_instance_as(copy.copy(ctx))
    assert not isl.DEFAULT_CONTEXT._wraps_same_instance_as(copy.copy(ctx))


def test_ast_node_list_free():
    # from https://github.com/inducer/islpy/issues/21
    # by Cambridge Yang

    ctx = isl.Context()
    schedule_map = isl.UnionMap.read_from_str(
            ctx, "[N] -> { S0[i] -> [i, 0] : "
            "0 <= i < N; S1[i] -> [i, 1] : 0 <= i < N }")
    ast_build = isl.AstBuild.from_context(isl.Set.read_from_str(ctx, "[N] -> { : }"))
    ast = ast_build.node_from_schedule_map(schedule_map)

    print(ast.to_C_str())
    # Prints below code:
    # for (int c0 = 0; c0 < N; c0 += 1) {
    #  S0(c0);
    #  S1(c0);
    # }

    # we have S0 and S1 in a ast_node_block, which holds "children" of type
    # ASTNodeList
    body = ast.for_get_body()
    assert body.get_type() == isl.ast_node_type.block

    body.block_get_children()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])
