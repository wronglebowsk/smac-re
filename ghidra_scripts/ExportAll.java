// ExportAll.java — batch-decompile every function of the analysed program.
//
// Goal: stop paying a Ghidra session (~205 s import + interactive round-trips) for every
// question. After one export the whole corpus is greppable on disk:
//   ghidra_out/index.csv     one row per function: addr,name,size,insns,callers,...
//   ghidra_out/shard_NNN.c   decompiled C, SHARD functions per file, each prefixed with
//                            "// ==== NAME @ ADDR size=N" so sed/awk can slice by function.
//
// Env: SMAC_EXPORT_DIR (default ~/reverse/smac/ghidra_out)
//      SMAC_MAX_SECONDS (default 5400) — hard budget; the script stops cleanly and says so.
// Progress lines "progress <n> <name>" go to stdout (captured by analyzeHeadless).
//@category SMAC

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public class ExportAll extends GhidraScript {

    private static final int SHARD = 250;

    @Override
    public void run() throws Exception {
        String outDir = System.getenv("SMAC_EXPORT_DIR");
        if (outDir == null || outDir.isEmpty()) {
            outDir = System.getProperty("user.home") + "/reverse/smac/ghidra_out";
        }
        long maxSeconds = 5400;
        String ms = System.getenv("SMAC_MAX_SECONDS");
        if (ms != null && !ms.isEmpty()) {
            maxSeconds = Long.parseLong(ms);
        }
        new File(outDir).mkdirs();
        long t0 = System.currentTimeMillis();

        DecompInterface ifc = new DecompInterface();
        ifc.setOptions(new DecompileOptions());
        ifc.toggleCCode(true);
        ifc.toggleSyntaxTree(false);
        if (!ifc.openProgram(currentProgram)) {
            println("FATAL: decompiler could not open the program");
            return;
        }

        PrintWriter idx = new PrintWriter(new BufferedWriter(
                new FileWriter(outDir + "/index.csv")));
        idx.println("addr,name,size_bytes,n_insns,n_callers,n_callees,n_strings,ok,chars,shard");

        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        int n = 0, okCount = 0, shardNo = -1, charsTotal = 0;
        PrintWriter shard = null;
        boolean budgetHit = false;

        while (fit.hasNext()) {
            if ((System.currentTimeMillis() - t0) / 1000 > maxSeconds) {
                budgetHit = true;
                break;
            }
            Function f = fit.next();
            String name = f.getName();
            long addr = f.getEntryPoint().getOffset();
            long size = f.getBody().getNumAddresses();

            if (n % SHARD == 0) {
                if (shard != null) {
                    shard.close();
                }
                shardNo++;
                shard = new PrintWriter(new BufferedWriter(
                        new FileWriter(String.format("%s/shard_%03d.c", outDir, shardNo))));
            }

            int insns = 0;
            InstructionIterator ii = currentProgram.getListing().getInstructions(f.getBody(), true);
            Set<Long> stringAddrs = new HashSet<>();
            while (ii.hasNext()) {
                Instruction ins = ii.next();
                insns++;
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    Reference[] refs = ins.getOperandReferences(op);
                    for (Reference r : refs) {
                        if (r.getToAddress() != null && !r.getToAddress().isExternalAddress()) {
                            var d = currentProgram.getListing().getDataAt(r.getToAddress());
                            if (d != null && d.hasStringValue()) {
                                stringAddrs.add(r.getToAddress().getOffset());
                            }
                        }
                    }
                }
            }

            int callers = 0;
            ReferenceIterator rit = currentProgram.getReferenceManager()
                    .getReferencesTo(f.getEntryPoint());
            while (rit.hasNext()) {
                rit.next();
                callers++;
            }
            int callees = f.getCalledFunctions(monitor).size();

            DecompileResults res = ifc.decompileFunction(f, 60, monitor);
            String c = null;
            boolean ok = false;
            if (res != null && res.decompileCompleted()) {
                var df = res.getDecompiledFunction();
                if (df != null) {
                    c = df.getC();
                    ok = c != null && !c.isEmpty();
                }
            }
            if (!ok) {
                c = "// decompile failed\n";
            } else {
                okCount++;
            }
            charsTotal += c.length();
            shard.println("// ==== " + name + " @ 0x" + Long.toHexString(addr) + " size=" + size);
            shard.print(c);
            shard.println();

            idx.printf(Locale.ROOT, "0x%08x,%s,%d,%d,%d,%d,%d,%s,%d,%03d%n",
                    addr, name, size, insns, callers, callees, stringAddrs.size(),
                    ok ? "1" : "0", c.length(), Math.max(shardNo, 0));

            n++;
            if (n % 250 == 0) {
                println("progress " + n + " " + name + " ok=" + okCount
                        + " mb=" + (charsTotal / (1024 * 1024)));
            }
        }

        if (shard != null) {
            shard.close();
        }
        idx.close();

        PrintWriter man = new PrintWriter(new FileWriter(outDir + "/MANIFEST.txt"));
        man.println("program: " + currentProgram.getName());
        man.println("functions: " + n);
        man.println("decompiled_ok: " + okCount);
        man.println("shards: " + (shardNo + 1));
        man.println("chars: " + charsTotal);
        man.println("seconds: " + ((System.currentTimeMillis() - t0) / 1000));
        man.println("budget_hit: " + budgetHit + " (limit " + maxSeconds + "s)");
        man.println("image_base: " + currentProgram.getImageBase());
        man.close();
        println("DONE functions=" + n + " ok=" + okCount + " shards=" + (shardNo + 1)
                + " budget_hit=" + budgetHit);
    }
}
