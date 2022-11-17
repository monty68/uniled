# SP61xE LED Controllers

The **SP61xE** are a range of small and cheap BLE controllers for addressable LEDs (pixels)

![SP61xE][SP61xE]

## SP611E LED Controller

The SP611E supports 3 color RGB chipsets: WS2811, WS2812B, WS2813, WS2815, LC8808B, GS8208, SK6812, SM16703 and UCS1903.

## SP617E LED Controller

The SP617E supports 4 color RGBW chipsets: SK6812, SM16704, UCS2904, WS2814 and TM1824

## BLE configuration

The service can be found with UUID `ffe0`. Under this is (at least) the , `0000ffe1-0000-1000-8000-00805f9b34fb` 
characteristic used to send commands and receive any responses.

*Note, this entire guide uses hexidecimal notation unless otherwise stated.*

# Command Message Format

All command messages begin with three bytes:

1.  `HB` - Header Byte, always `0xA0`, indicating start of a command message.
2.  `C#` - One of the valid command numbers.
3.  `D#` - Number of Data Bytes that follows.

---
## Informational Commands
<details><summary>Request Status</summary>
<p>

| Command | `0x70` |
| ----------- | ----------- |
| Action | Returns State Packet(s) |
| Length | 3 |
| Format | `HB C# D#` |
| Example | `A0 70 00` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `70`
3.  `D#` - Data Bytes to follow, always `00`
</p>
</details>

<details><summary>State Packets</summary>
<p>

| State Packet |#1 |
| ----------- | ----------- |
| Length | 20 |
| Format | `H1 H2 P# FT D# PS SN EN ?? LV ES EL RR GG BB IN IG ?? ?? ??` |
| Example | `53 43 01 17 0f 00 00 cd 02 ff 0a 96 ff 00 00 00 10 09 04 0b` |
**Fields**
1.  `H1` - Header Byte 1, always `53` (Ascii `S`)
2.  `H2` - Header Byte 2, always `43` (Ascii `P`)
3.  `P#` - Packet Number, always `01`
4.  `FT` - Frame Type, `0x17` = Single, `0x18` = Double, `0x19` = Triple
5.  `D#` - Data Bytes to follow, should always be 0x0F6.  `PS` - **Power State** (0x00 = Off, 0x01 = On)
7.  `SN` - **Scene Number** (Note Used, always 0x00)
8.  `EN` - **Effect Number** (See Effects List below)
9.  `??`
10. `LV` - **Brightness Level** (0x00 - 0xFF)
11. `ES` - **Effect Speed** (0x00 - 0x0A)
12. `EL` - **Effect Length** (0x00 - 0x96)
13. `RR` - **Red Level** (0x00 - 0xFF)
14. `GG` - **Green Level** (0x00 - 0xFF)
15. `BB` - **Blue Level** (0x00 - 0xFF)
16. `IN` - **Input** for sound actvated effects (0x00 = Int. Mic, 0x01 = Player, 0x02 = Ext. Mic)
17. `IG` - **Input Gain/Sensitivity** (0x00 - 0x0F)
18. `??`
19. `??`
20. `??`

| State Packet | #2 |
| ----------- | ----------- |
| Length | 14 |
| Format |  `H1 H2 P# FT D# ?? ?? ?? RR GG BB ?? ?? ??` |
| Example | `53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00` |
**Fields**
1.  `H1` - Header Byte 1, always `53` (Ascii `S`)
2.  `H2` - Header Byte 2, always `43` (Ascii `P`)
3.  `P#` - Packet Number, always `02`
4.  `FT` - Frame Type, `0x17` = Single, `0x18` = Double, `0x19` = Triple
5.  `D#` - Data Bytes to follow, should always be 0x0F6.  `??`
7.  `??`
8.  `??`
9.  `RR` - **Red Level** (0x00 - 0xFF) for Channel 2?
10. `GG` - **Green Level** (0x00 - 0xFF) for Channel 2?
11. `BB` - **Blue Level** (0x00 - 0xFF) for Channel 2?
12. `??`
13. `??`
14. `??`
</p>
</details>

## Configuration Commands
<details><summary>Set Device Name</summary>
<p>

| Command | `0x61` |
| ----------- | ----------- |
| Action | Change device name|
| Length | Max 13 (3 for command followed by up to 10 characters) |
| Format | `HB C# D# N0 N1 N2 N3 N4 N5 N6 N7 N8 N9` |
| Example | `a0 61 06 6f 66 66 69 63 65` - Sets name to "office" |

**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `61`
3.  `D#` - Data Bytes to follow, (0x00 - 0x0A)
4.  `N0-N9` - **Characters**
</p>
</details>


## Control Commands
<details><summary>Set Power State</summary>
<p>

| Command | `0x62` |
| ----------- | ----------- |
| Action | Turns power on or off|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 62 01 00` |

**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `62`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Power State** (0x00 = Off, 0x01 = On)
</p>
</details>

<details><summary>Set Effect</summary>
<p>

| Command | `0x63` |
| ----------- | ----------- |
| Action | Changes the effect/pattern|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 63 01 BE` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `63`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Effect Number** (See Effects List below)
### Effects List
- `01 - 8F` - Dynamic Effects
- `BE` - Static (Solid Color)
- `C9 - DA` - Music Effects
</p>
</details>

<details><summary>Set Brightness Level</summary>
<p>

| Command | `0x66` |
| ----------- | ----------- |
| Action | Changes the overall level of brightness|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 66 01 FF` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `66`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Brightness Level** (0x00 - 0xFF)
</p>
</details>

<details><summary>Set Effect Speed</summary>
<p>

| Command | `0x67` |
| ----------- | ----------- |
| Action | Changes the effect speed|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 67 01 0A` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `67`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Effect Speed** (0x00 - 0x0A)
</p>
</details>

<details><summary>Set Effect Length</summary>
<p>

| Command | `0x68` |
| ----------- | ----------- |
| Action | Changes the effect length|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 68 01 FF` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `68`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Effect Length** (0x00 - 0x96)
</p>
</details>

<details><summary>Set Color Levels</summary>
<p>

| Command | `0x69` |
| ----------- | ----------- |
| Action | Changes the color levels|
| Length | 7 |
| Format | `HB C# D# RR GG BB WW` |
| Example | `A0 69 04 00 FF 00 FF` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `69`
3.  `D#` - Data Bytes to follow, always `04`
4.  `RR` - **Red Level** (0x00 - 0xFF)
5.  `GG` - **Green Level** (0x00 - 0xFF)
6.  `BB` - **Blue Level** (0x00 - 0xFF)
7.  `WW` - **White Level** (0x00 - 0xFF) - *Note: Ignored on SP611E as it does not support RGBW LEDs*
</p>
</details>

<details><summary>Set Input Gain/Sensitivity</summary>
<p>

| Command | `0x6B` |
| ----------- | ----------- |
| Action | Changes the input sensitivity|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 6B 01 0F` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `6B`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Gain/Sensitivity** (0x01 - 0x0F)
</p>
</details>

<details><summary>Set Input</summary>
<p>

| Command | `0x6C` |
| ----------- | ----------- |
| Action | Changes the input for sound based effects|
| Length | 4 |
| Format | `HB C# D# VV` |
| Example | `A0 6C 01 01` |
**Fields**
1.  `HB` - Header Byte, always `A0`
2.  `C#` - Command Number, always `6C`
3.  `D#` - Data Bytes to follow, always `01`
4.  `VV` - **Input** (0x00 = Int. Mic, 0x01 = Player, 0x02 = Ext. Mic)
</p>
</details>

[SP61xE]: img/sp61xe.jpg