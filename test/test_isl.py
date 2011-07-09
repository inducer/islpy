from __future__ import division
import sys
import pytools.test




import islpy as isl




def test_basics():
    ctx = isl.Context()
    dim = isl.Dim(ctx, 3, 2, 1)
    print "YO"







if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
