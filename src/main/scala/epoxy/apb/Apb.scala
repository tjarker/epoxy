package epoxy.apb

import chisel3._

/** Parameters of an AMBA APB3 interface.
  *
  * @param addrWidth width of PADDR in bits, at most 32
  * @param dataWidth width of PWDATA and PRDATA in bits: 8, 16 or 32
  */
case class ApbParams(addrWidth: Int = 32, dataWidth: Int = 32) {
  require(addrWidth >= 1 && addrWidth <= 32, s"APB address width must be 1 to 32 bits, got $addrWidth")
  require(Set(8, 16, 32).contains(dataWidth), s"APB data width must be 8, 16 or 32 bits, got $dataWidth")
}

/** AMBA APB3 interface, seen from the requester.
  *
  * A requester uses it as is, a completer wraps it in `Flipped`. PCLK and PRESETn are the
  * module's implicit clock and reset. The APB4 and APB5 additions (PSTRB, PPROT, ...) are not
  * included, so every write updates the full data word.
  */
class ApbBundle(val params: ApbParams) extends Bundle {
  val psel = Output(Bool())
  val penable = Output(Bool())
  val pwrite = Output(Bool())
  val paddr = Output(UInt(params.addrWidth.W))
  val pwdata = Output(UInt(params.dataWidth.W))
  val prdata = Input(UInt(params.dataWidth.W))
  val pready = Input(Bool())
  val pslverr = Input(Bool())
}
