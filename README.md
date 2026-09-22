# epoxy

Chisel interface definitions and the IP that connects them, built for every Chisel version
from 3.5 to 7.

## Installation

Pick the artifact for your Chisel version from the [table below](#chisel-versions):

```scala
// sbt
libraryDependencies += "io.github.tjarker" %% "epoxy-chisel7" % "<version>"
// Mill
mvn"io.github.tjarker::epoxy-chisel7:<version>"
```

No version has been released yet; see [RELEASING.md](RELEASING.md).

## Contents

| Package | What |
|---|---|
| `epoxy.apb` | `ApbBundle` and `ApbParams`: AMBA APB3 (PSEL, PENABLE, PWRITE, PADDR, PWDATA, PRDATA, PREADY, PSLVERR) |
| `epoxy.wishbone` | `WishboneBundle` and `WishboneParams`: Wishbone B4 classic with only the mandatory signals (CYC, STB, WE, ADR, DAT, ACK) |
| `epoxy.bridge` | `WishboneToApb` and `ApbToWishbone` |

Bundles are defined from the requester's side; a completer wraps them in `Flipped`. Both
protocols use the module's implicit clock and reset.

```scala
import chisel3._
import epoxy.bridge.WishboneToApb

val bridge = Module(new WishboneToApb(addrWidth = 16, dataWidth = 32))
bridge.wb <> cpuBus          // a Wishbone requester's WishboneBundle
peripheralBus <> bridge.apb  // an APB completer's Flipped(ApbBundle)
```

What "basic" means here:

- **APB3 rather than the original APB**, because the bridges need PREADY to wait for the other
  side.
- **Full-word transfers only.** APB3 has no PSTRB and the basic Wishbone interface has no SEL.
- **No error reporting.** The basic Wishbone interface has no ERR, so `WishboneToApb` ignores
  PSLVERR and `ApbToWishbone` always drives it low.
- **Addresses pass through unchanged**, so both sides of a bridge use the same address and
  data width (at most 32 bits, the APB limit).
- `WishboneToApb` takes at least two cycles per transfer (APB setup and access phase).
  `ApbToWishbone` adds no latency and holds no state.

## Chisel versions

Chisel only keeps binary compatibility within a major version (within 3.5 and within 3.6 for
Chisel 3). epoxy is therefore built once per group, compiled against the group's oldest
release so that it works with all of them.

| sbt project | Artifact | Chisel versions | Built against | Scala |
|---|---|---|---|---|
| `chisel35` | `epoxy-chisel35` | 3.5.x | 3.5.6 | 2.13.10 |
| `chisel36` | `epoxy-chisel36` | 3.6.x | 3.6.1 | 2.13.14 |
| `chisel5` | `epoxy-chisel5` | 5.x | 5.0.0 | 2.13.10 |
| `chisel6` | `epoxy-chisel6` | 6.x | 6.0.0 | 2.13.12 |
| `chisel7` | `epoxy-chisel7` | 7.x | 7.0.0 | 2.13.16 |

Each Scala version is the newest one the Chisel compiler plugin of the base version was
published for. The groups are defined in [project/ChiselGroup.scala](project/ChiselGroup.scala).

CI also tests the Chisel 5, 6 and 7 groups against the newest release of each, every week and
before every release.

## Development

You need JDK 17 (some of the older Scala versions above do not run on newer JDKs), sbt,
Python with the packages in [tb/requirements.txt](tb/requirements.txt), and Icarus Verilog or
Verilator.

```bash
./test.sh                        # all groups
./test.sh chisel7                # one group
SIM=verilator ./test.sh chisel7  # use Verilator instead of Icarus Verilog
```

For each group, `test.sh` runs the Scala tests (every module compiles to Verilog), emits the
bridges' Verilog to `builds/<group>/verilog`, and runs the cocotb testbenches in [tb/](tb/)
on it. The testbenches check the APB and Wishbone protocols cycle by cycle, check that every
transfer arrives exactly once and in order, and run random traffic with random wait states.

Chisel 5 needs firtool on the PATH. The build fetches firtool 1.51.0 for its tests, the
oldest version on Maven Central; the versions Chisel 5 was released with (1.40 to 1.43) are
not published there.

| Path | What |
|---|---|
| `src/main/scala` | library code shared by all groups |
| `src/test/scala` | Scala tests and the Verilog generator for the testbenches |
| `src/test/scala-chisel3`, `src/test/scala-chisel5plus` | code that differs between Chisel 3 and Chisel 5+ |
| `tb/` | cocotb testbenches |
| `builds/` | per-group build output (not checked in) |
