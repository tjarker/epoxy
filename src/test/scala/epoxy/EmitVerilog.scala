package epoxy

import java.nio.file.{Files, Paths}

import epoxy.bridge.{ApbToWishbone, WishboneToApb}

/** Writes the Verilog simulated by the cocotb testbenches in tb/ into the given directory. */
object EmitVerilog {
  def main(args: Array[String]): Unit = {
    require(args.length == 1, "usage: EmitVerilog <output directory>")
    val outDir = Paths.get(args(0))
    Files.createDirectories(outDir)
    Files.write(outDir.resolve("WishboneToApb.sv"), mainFile(Emit.verilog(new WishboneToApb(32, 32))).getBytes)
    Files.write(outDir.resolve("ApbToWishbone.sv"), mainFile(Emit.verilog(new ApbToWishbone(32, 32))).getBytes)
  }

  /** Chisel 7 appends further files (verification layers) to the output, separated by marker
    * lines. They `include` each other by file name, so only the module itself is kept.
    */
  private def mainFile(verilog: String): String = verilog.split("// ----- 8< -----")(0)
}
