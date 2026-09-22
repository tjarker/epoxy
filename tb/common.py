"""Shared pieces of the bridge testbenches."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


async def start(dut):
    """Starts the clock and holds reset for two cycles. Returns right after a rising edge."""
    cocotb.start_soon(Clock(dut.clock, 10, units="ns").start())
    dut.reset.value = 1
    for _ in range(2):
        await RisingEdge(dut.clock)
    dut.reset.value = 0


def random_transfers(rng, count):
    """Returns `count` random (write, address, data, idle cycles afterwards) tuples.

    Addresses come from a small set so that reads often hit earlier writes. Half of the
    transfers are followed directly by the next one.
    """
    transfers = []
    for _ in range(count):
        write = rng.random() < 0.5
        address = rng.randrange(16) * 4
        data = rng.getrandbits(32) if write else 0
        gap = rng.choice([0, 0, 1, 2])
        transfers.append((write, address, data, gap))
    return transfers
