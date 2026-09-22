package epoxy.bridge

import chisel3._
import epoxy.apb.{ApbBundle, ApbParams}
import epoxy.wishbone.{WishboneBundle, WishboneParams}

/** Lets an APB requester access a Wishbone completer.
  *
  * The Wishbone transfer runs during the APB access phase and its ACK is passed back as
  * PREADY, so the bridge adds no latency and holds no state. PSLVERR is always low because the
  * basic Wishbone interface has no error signal.
  *
  * @param addrWidth address width of both interfaces, at most 32
  * @param dataWidth data width of both interfaces: 8, 16 or 32
  */
class ApbToWishbone(addrWidth: Int = 32, dataWidth: Int = 32) extends Module {
  val apb = IO(Flipped(new ApbBundle(ApbParams(addrWidth, dataWidth))))
  val wb = IO(new WishboneBundle(WishboneParams(addrWidth, dataWidth)))

  // PENABLE is low for at least one cycle after an APB transfer completes, so STB drops right
  // after ACK and a finished transfer is never repeated on the Wishbone side.
  val access = apb.psel && apb.penable
  wb.cyc := access
  wb.stb := access
  wb.we := apb.pwrite
  wb.adr := apb.paddr
  wb.datW := apb.pwdata

  apb.pready := wb.ack
  apb.prdata := wb.datR
  apb.pslverr := false.B
}
