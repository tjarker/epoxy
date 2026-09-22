package epoxy

import chisel3.RawModule
import circt.stage.ChiselStage

/** Verilog emission for Chisel 5 and later, which use firtool. */
object Emit {
  def verilog(gen: => RawModule): String =
    ChiselStage.emitSystemVerilog(gen, firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
}
