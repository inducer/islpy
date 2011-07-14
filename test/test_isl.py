from __future__ import division




import islpy as isl




def test_basics():
    dt = isl.dim_type

    ctx = isl.Context()
    dim = isl.Dim.create_from_names(ctx, set=["a", "b"])

    bset = (isl.BasicSet.universe(dim)
            .add_constraint(isl.Constraint.eq_from_names(dim, 0, dict(a=-1, b=2)))
            .add_constraint(isl.Constraint.ineq_from_names(dim, -10, dict(a=1)))
            .add_constraint(isl.Constraint.ineq_from_names(dim, 42, dict(a=-1)))
            .project_out(dt.set, 1, 1))
    print bset

    bset2 = isl.BasicSet.read_from_str(ctx,
            "{[i] : exists (a : i = 2a and i >= 10 and i <= 42)}", nparam=-1)

    mset = isl.Set.from_basic_set(bset2)
    points = []
    mset.foreach_point(points.append)

    for pt in points:
        print pt







if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
