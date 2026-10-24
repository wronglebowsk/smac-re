
import importlib.util
spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.init()
for idx in (44, 70, 58, 40, 37):
    m.G["dbg"] = idx
    o = m.rebuild(idx)
    m.G["dbg"] = None
    print("### idx %d fac %d pop %d pool %s model_processed %s | budget %d->%d c7c_in %d c80_end %d fresh %s obs %s vec %s" %
          (idx, o["fac"], o["pop"], hex(o["mask_in"]), hex(o["processed"]),
           o["budget0"], o["budget_end"], o["c7c_in"], o["c80_end"], hex(o["mask_fresh"]),
           list(o["obs"]), o["vec"]))
