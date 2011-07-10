from __future__ import division
import sys
import pytools.test




import islpy as isl




def test_basics():
    dt = isl.dim_type

    ctx = isl.Context()
    dim = isl.create_dim(ctx, set="ab")

    bset = isl.BasicSet.universe(dim.copy())
    bset.add_constraint(
            isl.create_equality_by_names(dim, 0, dict(a=-1, b=2)))
    bset.add_constraint(
            isl.create_inequality_by_names(dim, -10, dict(a=1)))
    bset.add_constraint(
            isl.create_inequality_by_names(dim, 42, dict(a=-1)))
    bset.project_out(dt.set, 1, 1)
    bset.dump()




if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
