import islpy as isl
from islpy import oppool as oppool


def test_pooled_basic_set_intersect():
    ctx = isl.DEFAULT_CONTEXT
    pool = oppool.ISLOpMemoizer()
    set1 = oppool.NormalizedISLBasicSet.read_from_str(ctx, "{[i]: 0<=i<10}")
    set2 = oppool.NormalizedISLBasicSet.read_from_str(ctx, "{[i]: 0<=i<5}")

    set3 = oppool.NormalizedISLBasicSet.read_from_str(ctx, "{[j]: 0<=j<10}")
    set4 = oppool.NormalizedISLBasicSet.read_from_str(ctx, "{[j]: 0<=j<5}")

    set1_and_set2 = set1.intersect(pool, set2)
    set3_and_set4 = set3.intersect(pool, set4)

    assert set1_and_set2.ground_obj is set3_and_set4.ground_obj


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])
