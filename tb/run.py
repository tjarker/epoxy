"""Runs the cocotb testbenches against the Verilog emitted for one Chisel group.

    python3 tb/run.py <verilog directory> [--sim icarus|verilator]

The Verilog comes from `sbt "<group>/Test/runMain epoxy.EmitVerilog <verilog directory>"`.
"""

import argparse
import sys
import warnings
from pathlib import Path

# cocotb 1.9 marks its Python runner as experimental and warns on import.
warnings.filterwarnings("ignore", message="Python runners")
from cocotb.runner import get_results, get_runner  # noqa: E402

TESTBENCHES = {
    "WishboneToApb": "test_wishbone_to_apb",
    "ApbToWishbone": "test_apb_to_wishbone",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("verilog_dir", type=Path)
    parser.add_argument("--sim", choices=["icarus", "verilator"], default="icarus")
    args = parser.parse_args()
    verilog_dir = args.verilog_dir.resolve()

    failed = 0
    for toplevel, test_module in TESTBENCHES.items():
        build_dir = verilog_dir / "sim" / args.sim / toplevel
        runner = get_runner(args.sim)
        runner.build(
            verilog_sources=[verilog_dir / f"{toplevel}.sv"],
            hdl_toplevel=toplevel,
            build_dir=build_dir,
            always=True,
            # Chisel emits no `timescale, which would leave the simulator at 1 s precision.
            timescale=("1ns", "1ps"),
        )
        results = runner.test(test_module=test_module, hdl_toplevel=toplevel, build_dir=build_dir)
        failed += get_results(results)[1]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
