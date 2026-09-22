"""Tests ApbToWishbone between an APB requester model and a Wishbone completer model."""

import random
from collections import deque

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from common import random_transfers, start


class ApbRequester:
    """Drives the bridge's APB port."""

    def __init__(self, dut):
        self.dut = dut
        dut.apb_psel.value = 0
        dut.apb_penable.value = 0
        dut.apb_pwrite.value = 0
        dut.apb_paddr.value = 0
        dut.apb_pwdata.value = 0

    async def transfer(self, write, address, data=0):
        """Runs one transfer and returns (read data, PSLVERR, access phase cycles).

        Starts right after a rising edge and returns right after the edge that completes the
        transfer. PSEL stays high, so the next transfer's setup phase can follow directly.
        """
        dut = self.dut
        dut.apb_psel.value = 1
        dut.apb_penable.value = 0
        dut.apb_pwrite.value = int(write)
        dut.apb_paddr.value = address
        dut.apb_pwdata.value = data
        await RisingEdge(dut.clock)
        dut.apb_penable.value = 1
        cycles = 1
        while True:
            await ReadOnly()
            if dut.apb_pready.value == 1:
                read_data = None if write else int(dut.apb_prdata.value)
                error = int(dut.apb_pslverr.value)
                break
            await RisingEdge(dut.clock)
            cycles += 1
        await RisingEdge(dut.clock)
        dut.apb_penable.value = 0
        return read_data, error, cycles

    async def idle(self, cycles):
        self.dut.apb_psel.value = 0
        self.dut.apb_penable.value = 0
        for _ in range(cycles):
            await RisingEdge(self.dut.clock)


class WishboneCompleter:
    """Memory-backed Wishbone completer that raises ACK 1 to 1 + `max_wait` cycles after STB.

    Checks the Wishbone protocol on every cycle, and that the transfers it receives match
    `expected`, in order.
    """

    def __init__(self, dut, rng, max_wait):
        self.dut = dut
        self.rng = rng
        self.max_wait = max_wait
        self.memory = {}
        self.expected = deque()
        self.completed = 0
        dut.wb_ack.value = 0
        dut.wb_datR.value = 0
        cocotb.start_soon(self._run())

    async def _run(self):
        dut = self.dut
        previous_phase, previous_request, waits = "idle", None, 0
        while True:
            await ReadOnly()
            if dut.reset.value == 1:
                await RisingEdge(dut.clock)
                continue

            cyc, stb, ack = int(dut.wb_cyc.value), int(dut.wb_stb.value), int(dut.wb_ack.value)
            request = (int(dut.wb_we.value), int(dut.wb_adr.value), int(dut.wb_datW.value)) if stb else None

            assert cyc or not stb, "STB is high without CYC"
            if previous_phase == "wait":
                assert stb, "STB dropped before ACK"
                assert request == previous_request, "request changed before ACK"

            if not stb:
                phase = "idle"
            elif ack:
                phase = "done"
            else:
                phase = "wait"

            if phase == "done":
                self._complete(request)
            if phase == "wait":
                waits = waits - 1 if previous_phase == "wait" else self.rng.randint(0, self.max_wait)
            next_ack = phase == "wait" and waits == 0
            if next_ack and not request[0]:
                next_data = self.memory.get(request[1], 0)
            else:
                next_data = self.rng.getrandbits(32)

            previous_phase, previous_request = phase, request
            await RisingEdge(dut.clock)
            dut.wb_ack.value = int(next_ack)
            dut.wb_datR.value = next_data

    def _complete(self, request):
        assert self.expected, f"unexpected Wishbone transfer {request}"
        write, address, data = request
        expected_write, expected_address, expected_data = self.expected.popleft()
        assert (write, address) == (expected_write, expected_address), (
            f"Wishbone transfer (write={write}, address={address:#x}), "
            f"expected (write={expected_write}, address={expected_address:#x})"
        )
        if write:
            assert data == expected_data, f"Wishbone write data {data:#x}, expected {expected_data:#x}"
            self.memory[address] = data
        self.completed += 1


@cocotb.test(timeout_time=50, timeout_unit="us")
async def no_added_latency(dut):
    """The APB access phase lasts exactly as long as the Wishbone transfer (two cycles here)."""
    requester = ApbRequester(dut)
    completer = WishboneCompleter(dut, random.Random(cocotb.RANDOM_SEED), max_wait=0)
    await start(dut)

    transfers = [(True, 0x10, 0x12345678), (False, 0x10, 0), (True, 0x14, 0xCAFEF00D), (False, 0x14, 0)]
    results = []
    for write, address, data in transfers:
        completer.expected.append((int(write), address, data))
        results.append(await requester.transfer(write, address, data))
    await requester.idle(2)

    assert [cycles for _, _, cycles in results] == [2, 2, 2, 2]
    assert results[1][0] == 0x12345678
    assert results[3][0] == 0xCAFEF00D
    assert completer.completed == len(transfers)


@cocotb.test(timeout_time=1, timeout_unit="ms")
async def random_traffic(dut):
    """Random reads and writes with random Wishbone wait states and random gaps between transfers."""
    rng = random.Random(cocotb.RANDOM_SEED)
    requester = ApbRequester(dut)
    completer = WishboneCompleter(dut, rng, max_wait=3)
    await start(dut)

    reference = {}
    transfers = random_transfers(rng, count=500)
    for write, address, data, gap in transfers:
        completer.expected.append((int(write), address, data))
        read_data, error, _ = await requester.transfer(write, address, data)
        assert error == 0, "PSLVERR must always be low"
        if write:
            reference[address] = data
        else:
            expected = reference.get(address, 0)
            assert read_data == expected, f"read {address:#x} returned {read_data:#x}, expected {expected:#x}"
        if gap:
            await requester.idle(gap)
    await requester.idle(2)

    assert completer.completed == len(transfers)
    assert not completer.expected
