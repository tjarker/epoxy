package epoxy

import chisel3.RawModule
import chisel3.stage.ChiselStage

/** Verilog emission for Chisel 3, which uses its built-in Scala FIRRTL compiler. */
object Emit {
  def verilog(gen: => RawModule): String = (new ChiselStage).emitVerilog(gen)
}
