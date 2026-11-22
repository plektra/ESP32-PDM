"""Title blocks of the pdm-4ch schematics and PCB (decision 220: licence and source location).

    python3 hardware/pdm-4ch/scripts/title_block.py            schematics, through tools/ksch.py
    <KiCad python> hardware/pdm-4ch/scripts/title_block.py     also the PCB, through pcbnew (run with KiCad closed)

Same text as the bottom silkscreen (scripts/silk.py: REV, SOURCE). Verify the schematics with ERC and a netlist
compare, the PCB with DRC."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BOARD_DIR, '..', '..', 'tools'))

TITLE = 'ESP32-PDM pdm-4ch'
DATE = '2026-11'
REV = 'A'
COMMENTS = ('Hardware licence: CERN-OHL-S v2', 'Source: github.com/plektra/ESP32-PDM')
SHEETS = {'ESP32-PDM-4CH.kicad_sch': '', 'power-usb.kicad_sch': 'Power and USB',
          'analog_sw.kicad_sch': 'Analog interface', 'channel.kicad_sch': 'Channel 1-4',
          'can.kicad_sch': 'CAN'}

try:
    import pcbnew
except ImportError:
    pcbnew = None

if pcbnew is None:
    import ksch
    for fn, sub in SHEETS.items():
        path = os.path.join(BOARD_DIR, fn)
        t = ksch.load(path)
        ksch.set_title_block(t, TITLE + (': ' + sub if sub else ''), DATE, REV, comments=COMMENTS)
        ksch.save(t, path)
        print('title block:', fn)
else:
    path = os.path.join(BOARD_DIR, 'ESP32-PDM-4CH.kicad_pcb')
    b = pcbnew.LoadBoard(path)
    tb = b.GetTitleBlock()
    tb.SetTitle(TITLE); tb.SetDate(DATE); tb.SetRevision(REV)
    for i, c in enumerate(COMMENTS):
        tb.SetComment(i, c)
    b.SetTitleBlock(tb)
    pcbnew.SaveBoard(path, b)
    print('title block: ESP32-PDM-4CH.kicad_pcb')
