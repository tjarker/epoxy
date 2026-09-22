#!/usr/bin/env bash
# Runs all tests for the given Chisel groups (default: all of them): the Scala tests, then the
# cocotb testbenches on the Verilog each group emits. Needs JDK 17, sbt, Python with cocotb
# (tb/requirements.txt) and Icarus Verilog, or Verilator with SIM=verilator.
#
#   ./test.sh                      all groups
#   SIM=verilator ./test.sh chisel7
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -eq 0 ]; then
  set -- chisel35 chisel36 chisel5 chisel6 chisel7
fi

commands=()
for group in "$@"; do
  commands+=("$group/test" "$group/Test/runMain epoxy.EmitVerilog $PWD/builds/$group/verilog")
done
sbt "${commands[@]}"

for group in "$@"; do
  echo "== cocotb: $group"
  python3 tb/run.py "builds/$group/verilog" --sim "${SIM:-icarus}"
done
