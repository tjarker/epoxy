"""Tests WishboneToApb between a Wishbone requester model and an APB completer model."""

import random
from collections import deque

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge

from common import random_transfers, start


class WishboneRequester:
    """Drives the bridge's Wishbone port."""

    def __init__(self, dut):
        self.dut = dut
        dut.wb_cyc.value = 0
        dut.wb_stb.value = 0
        dut.wb_we.value = 0
        dut.wb_adr.value = 0
        dut.wb_datW.value = 0

    async def transfer(self, write, address, data=0):
        """Runs one transfer and returns (read data, cycles until ACK).

        Starts right after a rising edge and returns right after the edge that completes the
        transfer. The request stays driven, so the next transfer can follow back-to-back.
        """
        dut = self.dut
        dut.wb_cyc.value = 1
        dut.wb_stb.value = 1
        dut.wb_we.value = int(write)
        dut.wb_adr.value = address
        dut.wb_datW.value = data
        cycles = 1
        while True:
            await ReadOnly()
            if dut.wb_ack.value == 1:
                read_data = None if write else int(dut.wb_datR.value)
                break
            await RisingEdge(dut.clock)
            cycles += 1
        await RisingEdge(dut.clock)
        return read_data, cycles

    async def idle(self, cycles):
        self.dut.wb_cyc.value = 0
        self.dut.wb_stb.value = 0
        for _ in range(cycles):
            await ReadOnly()
            assert self.dut.wb_ack.value == 0, "ACK without a request"
            await RisingEdge(self.dut.clock)


class ApbCompleter:
    """Memory-backed APB completer that inserts 0 to `max_wait` random wait states.

    Checks the APB protocol on every cycle, and that the transfers it receives match
    `expected`, in order.
    """

    def __init__(self, dut, rng, max_wait):
        self.dut = dut
        self.rng = rng
        self.max_wait = max_wait
        self.memory = {}
        self.expected = deque()
        self.completed = 0
        dut.apb_pready.value = 0
        dut.apb_pslverr.value = 0
        dut.apb_prdata.value = 0
        cocotb.start_soon(self._run())

    async def _run(self):
        dut = self.dut
        previous_phase, previous_request, waits = "idle", None, 0
        while True:
            await ReadOnly()
            if dut.reset.value == 1:
                await RisingEdge(dut.clock)
                continue

            sel, enable, ready = int(dut.apb_psel.value), int(dut.apb_penable.value), int(dut.apb_pready.value)
            request = (int(dut.apb_pwrite.value), int(dut.apb_paddr.value), int(dut.apb_pwdata.value)) if sel else None

            assert sel or not enable, "PENABLE is high without PSEL"
            if previous_phase in ("setup", "wait"):
                assert sel and enable, f"{previous_phase} cycle not followed by an access cycle"
                assert request == previous_request, "request changed during the transfer"
            else:
                assert not enable, "access cycle without a setup cycle before it"

            if not sel:
                phase = "idle"
            elif not enable:
                phase = "setup"
            elif ready:
                phase = "done"
            else:
                phase = "wait"

            if phase == "done":
                self._complete(request)
            if phase == "setup":
                waits = self.rng.randint(0, self.max_wait)
            elif phase == "wait":
                waits -= 1
            next_ready = phase in ("setup", "wait") and waits == 0
            if next_ready and not request[0]:
                next_data = self.memory.get(request[1], 0)
            else:
                next_data = self.rng.getrandbits(32)

            previous_phase, previous_request = phase, request
            await RisingEdge(dut.clock)
            dut.apb_pready.value = int(next_ready)
            dut.apb_prdata.value = next_data

    def _complete(self, request):
        assert self.expected, f"unexpected APB transfer {request}"
        write, address, data = request
        expected_write, expected_address, expected_data = self.expected.popleft()
        assert (write, address) == (expected_write, expected_address), (
            f"APB transfer (write={write}, address={address:#x}), "
            f"expected (write={expected_write}, address={expected_address:#x})"
        )
        if write:
            assert data == expected_data, f"APB write data {data:#x}, expected {expected_data:#x}"
            self.memory[address] = data
        self.completed += 1


@cocotb.test(timeout_time=50, timeout_unit="us")
async def minimum_latency(dut):
    """Without APB wait states, every transfer takes two cycles, also back-to-back."""
    requester = WishboneRequester(dut)
    completer = ApbCompleter(dut, random.Random(cocotb.RANDOM_SEED), max_wait=0)
    await start(dut)

    transfers = [(True, 0x10, 0x12345678), (False, 0x10, 0), (True, 0x14, 0xCAFEF00D), (False, 0x14, 0)]
    results = []
    for write, address, data in transfers:
        completer.expected.append((int(write), address, data))
        results.append(await requester.transfer(write, address, data))
    await requester.idle(2)

    assert [cycles for _, cycles in results] == [2, 2, 2, 2]
    assert results[1][0] == 0x12345678
    assert results[3][0] == 0xCAFEF00D
    assert completer.completed == len(transfers)


@cocotb.test(timeout_time=1, timeout_unit="ms")
async def random_traffic(dut):
    """Random reads and writes with random APB wait states and random gaps between transfers."""
    rng = random.Random(cocotb.RANDOM_SEED)
    requester = WishboneRequester(dut)
    completer = ApbCompleter(dut, rng, max_wait=3)
    await start(dut)

    reference = {}
    transfers = random_transfers(rng, count=500)
    for write, address, data, gap in transfers:
        completer.expected.append((int(write), address, data))
        read_data, _ = await requester.transfer(write, address, data)
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
