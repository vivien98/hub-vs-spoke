"""Topology implementations for the benchmark harness.

Includes the three active benchmark topologies plus the legacy peer mesh
kept from earlier experiments.
"""

from hub_vs_spoke.topologies.base import Topology
from hub_vs_spoke.topologies.hub_spoke import HubSpokeTopology
from hub_vs_spoke.topologies.market import MarketTopology
from hub_vs_spoke.topologies.solo import SoloTopology
from hub_vs_spoke.topologies.spoke_spoke import SpokeSpokeTopology

__all__ = [
    "Topology",
    "SoloTopology",
    "HubSpokeTopology",
    "MarketTopology",
    "SpokeSpokeTopology",
]
