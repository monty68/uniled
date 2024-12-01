"""UniLED NET Devices - SP LED (BanlanX SP801E)"""

from __future__ import annotations
from typing import Final
from .device import UniledNetModel, UniledNetDevice


##
## BanlanX - SP801E Protocol Implementation
##
class SP801E(UniledNetModel):
    """BanlanX - SP801E Protocol Implementation - Currently not supported!"""

    MANUFACTURER_NAME: Final = "SPLED (BanlanX)"

    def __init__(self):
        super().__init__(
            model_code=0x9D01,  #0x9D
            model_name="SP801E",
            model_info="WiFi Art-Net Digital LED COntroller",
            manufacturer=self.MANUFACTURER_NAME,
            channels=1,
            net_port=0,
            net_close=False,
        )
