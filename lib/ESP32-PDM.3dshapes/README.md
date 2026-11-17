# ESP32-PDM 3D models

STEP models for footprints whose model is not in KiCad's stock library. Each file is named after the footprint that
uses it and is referenced as `${KIPRJMOD}/../../lib/ESP32-PDM.3dshapes/<footprint>.step`.

| File | Part | LCSC | Used by |
|---|---|---|---|
| `Infineon_PG-TDSO-14_ThermalVias.step` | BTT6050-1ERA (PG-TDSO-14) | C534868 | pdm-4ch U11–U14 |
| `Kefa_KF135T-10.16-2P.step` | Kefa KF135T-10.16-2P | C475108 | pdm-4ch J10 |
| `Kefa_KF2EDGRC-5.08-4P.step` | Kefa KF2EDGRC-5.08-4P | C441238 | pdm-4ch J11 |
| `Kangnex_WJ15EDGRC-3.81-04P.step` | Kangnex WJ15EDGRC-3.81-04P | C7245 | pdm-4ch J4 |
| `Kangnex_WJ15EDGRC-3.81-10P.step` | Kangnex WJ15EDGRC-3.81-10P | C26895 | pdm-4ch J5 |
| `USB_C_Receptacle_HRO_TYPE-C-31-M-12.step` | HRO TYPE-C-31-M-12 | C165948 | pdm-4ch J3 |
| `SW_Push_1P1T_XKB_TS-1187A.step` | XKB TS-1187A | C318884 | pdm-4ch SW_BOOT1, SW_RESET1 |
| `Fuse_1812_4532Metric.step` | mSMD050-60V (1812) | C70113 | pdm-4ch F1–F4 |
| `ESP32-S2-MINI-1.step` | ESP32-S3-MINI-1 (same outline as the S2 footprint) | C2913206 | pdm-4ch U1 |

Source: the LCSC/EasyEDA 3D model of each part, downloaded with `easyeda2kicad --3d --lcsc_id <id>`.

Placement: offset and rotation in each footprint come from fitting the EasyEDA footprint's pads onto ours (pad
numbers), corrected for the EasyEDA STEP origin (the STEP is centred on the body; the EasyEDA WRL is not). Each was
checked in a `kicad-cli pcb render`.

The last four footprints come from KiCad's stock library, whose model file is missing in KiCad 10. Only the board
instances point here; "Update footprints from library" would reset them to the missing stock path.
