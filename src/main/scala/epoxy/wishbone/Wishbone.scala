package epoxy.wishbone

import chisel3._

/** Parameters of a Wishbone B4 classic interface.
  *
  * @param addrWidth width of ADR in bits
  * @param dataWidth width of DAT in bits: 8, 16, 32 or 64
  */
case class WishboneParams(addrWidth: Int = 32, dataWidth: Int = 32) {
  require(addrWidth >= 1, s"Wishbone address width must be at least 1 bit, got $addrWidth")
  require(Set(8, 16, 32, 64).contains(dataWidth), s"Wishbone data width must be 8, 16, 32 or 64 bits, got $dataWidth")
}

/** Wishbone B4 classic interface with only the mandatory signals, seen from the requester
  * (the master in the Wishbone specification).
  *
  * A requester uses it as is, a completer wraps it in `Flipped`. CLK and RST are the module's
  * implicit clock and reset. There is no SEL, so every transfer moves a full data word, and the
  * optional ERR, RTY, LOCK and tag signals are not included.
  */
class WishboneBundle(val params: WishboneParams) extends Bundle {
  val cyc = Output(Bool())
  val stb = Output(Bool())
  val we = Output(Bool())
  val adr = Output(UInt(params.addrWidth.W))
  /** DAT_O of the requester. */
  val datW = Output(UInt(params.dataWidth.W))
  /** DAT_I of the requester. */
  val datR = Input(UInt(params.dataWidth.W))
  val ack = Input(Bool())
}
