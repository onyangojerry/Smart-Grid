# Author: Jerry Onyango
# Contribution: Validates profile decoding behavior for scale factors, byte order, and word order handling.
from __future__ import annotations

import unittest

from energy_api.edge.decoder import Decoder
from energy_api.edge.types import PointMapping


class TestDecoderProfiles(unittest.TestCase):
    def test_uint16_scale_factor(self) -> None:
        mapping = PointMapping(
            canonical_key="battery_soc",
            register_address=0,
            register_count=1,
            value_type="uint16",
            scale_factor=0.1,
        )
        decoded = Decoder.decode(mapping, [650])
        self.assertEqual(decoded.value, 65.0)

    def test_int16_signed(self) -> None:
        mapping = PointMapping(
            canonical_key="battery_power_kw",
            register_address=1,
            register_count=1,
            value_type="int16",
            signed=True,
            scale_factor=0.1,
        )
        decoded = Decoder.decode(mapping, [0xFFEC])
        self.assertAlmostEqual(decoded.value, -2.0, places=4)

    def test_float32_word_order_little(self) -> None:
        mapping = PointMapping(
            canonical_key="site_load_kw",
            register_address=2,
            register_count=2,
            value_type="float32",
            byte_order="big",
            word_order="little",
        )
        # Represents float32 12.5 encoded as big-endian words reversed at transport.
        decoded = Decoder.decode(mapping, [0x0000, 0x4148])
        self.assertAlmostEqual(decoded.value, 12.5, places=4)


if __name__ == "__main__":
    unittest.main()
