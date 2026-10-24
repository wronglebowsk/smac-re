
import importlib.util
spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.init()
print("idx fac popd saved_c7c plain_end plain_sc rec_end rec_sc drift rec_vec_delta")
sig = {}
for i in range(76):
    p = m.rebuild(i)                      # plain (pop = dump)
    r = m.recover_pop(i)                  # with pop-drift probe
    vd = [r["vec"][f] - list(r["obs"])[f] for f in range(4)]
    sig[i] = (p["budget_end"], p["c7c_in"], p["mask_in"] == p["processed"],
              r["budget_end"], r["mask_in"] == r["processed"], r["pop_drift"],
              [d for f, d in enumerate(vd) if d])
    if p["budget_end"] != p["c7c_in"] or p["mask_in"] != p["processed"] or any(vd):
        print("idx %2d fac %d popd %d saved_c7c %d plain_end %d plain_sc %d rec_end %d rec_sc %d drift %d vd %s"
              % (i, r["fac"], r["pop_dump"], p["c7c_in"], p["budget_end"],
                 int(p["mask_in"] == p["processed"]), r["budget_end"],
                 int(r["mask_in"] == r["processed"]), r["pop_drift"], vd))
sc = sum(1 for i in range(76) if sig[i][4]); ex = sum(1 for i in range(76) if sig[i][4] and not sig[i][6])
print("RECOVERED: rows 76 self-consistent %d; drift-recovered %d" % (sc, sum(1 for i in range(76) if sig[i][5])))
