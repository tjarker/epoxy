package epoxy

import epoxy.apb.ApbParams
import epoxy.bridge.{ApbToWishbone, WishboneToApb}
import epoxy.wishbone.WishboneParams
import org.scalatest.flatspec.AnyFlatSpec

/** Compiles every module to Verilog. Functional behavior is covered by the cocotb testbenches
  * in tb/.
  */
class ElaborationSpec extends AnyFlatSpec {
  private val widths = Seq((1, 8), (12, 16), (32, 32))

  // The cocotb testbenches address ports by these names, so they must be the same under
  // every Chisel version.
  private val apbPorts = Seq("apb_psel", "apb_penable", "apb_pwrite", "apb_paddr", "apb_pwdata", "apb_prdata", "apb_pready", "apb_pslverr")
  private val wishbonePorts = Seq("wb_cyc", "wb_stb", "wb_we", "wb_adr", "wb_datW", "wb_datR", "wb_ack")

  "WishboneToApb" should "compile to Verilog with stable port names" in {
    for ((addrWidth, dataWidth) <- widths) {
      val verilog = Emit.verilog(new WishboneToApb(addrWidth, dataWidth))
      for (port <- apbPorts ++ wishbonePorts) assert(verilog.contains(port), s"missing port $port")
    }
  }

  "ApbToWishbone" should "compile to Verilog with stable port names" in {
    for ((addrWidth, dataWidth) <- widths) {
      val verilog = Emit.verilog(new ApbToWishbone(addrWidth, dataWidth))
      for (port <- apbPorts ++ wishbonePorts) assert(verilog.contains(port), s"missing port $port")
    }
  }

  "ApbParams" should "reject widths APB does not allow" in {
    assertThrows[IllegalArgumentException](ApbParams(addrWidth = 33))
    assertThrows[IllegalArgumentException](ApbParams(dataWidth = 64))
  }

  "WishboneParams" should "reject widths Wishbone does not allow" in {
    assertThrows[IllegalArgumentException](WishboneParams(addrWidth = 0))
    assertThrows[IllegalArgumentException](WishboneParams(dataWidth = 24))
  }
}
