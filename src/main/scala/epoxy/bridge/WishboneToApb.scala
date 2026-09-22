package epoxy.bridge

import chisel3._
import epoxy.apb.{ApbBundle, ApbParams}
import epoxy.wishbone.{WishboneBundle, WishboneParams}

/** Lets a Wishbone requester access an APB completer.
  *
  * Each Wishbone transfer becomes one APB transfer. The APB setup phase happens in the cycle
  * the Wishbone request appears, followed by access cycles until the completer raises PREADY;
  * ACK is given in that same cycle. A transfer therefore takes at least two cycles.
  *
  * Address, direction and write data pass straight through. This relies on the Wishbone rule
  * that a requester holds them stable until ACK. The basic Wishbone interface has no error
  * signal, so PSLVERR is ignored.
  *
  * @param addrWidth address width of both interfaces, at most 32
  * @param dataWidth data width of both interfaces: 8, 16 or 32
  */
class WishboneToApb(addrWidth: Int = 32, dataWidth: Int = 32) extends Module {
  val wb = IO(Flipped(new WishboneBundle(WishboneParams(addrWidth, dataWidth))))
  val apb = IO(new ApbBundle(ApbParams(addrWidth, dataWidth)))

  val inAccess = RegInit(false.B)
  val setup = !inAccess && wb.cyc && wb.stb
  when(setup) {
    inAccess := true.B
  }.elsewhen(inAccess && apb.pready) {
    inAccess := false.B
  }

  apb.psel := setup || inAccess
  apb.penable := inAccess
  apb.pwrite := wb.we
  apb.paddr := wb.adr
  apb.pwdata := wb.datW

  wb.ack := inAccess && apb.pready
  wb.datR := apb.prdata
}
