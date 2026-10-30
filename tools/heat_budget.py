#!/usr/bin/env python3
"""Steady-state heat budget for an ESP32-PDM board in its enclosure.

Model: every channel dissipates I^2 * Rds(on)(Tj); the enclosure air rises by
P_total * R_box above ambient; each switch junction sits P_channel * RthJA above
the enclosure air. Rds(on) rises linearly with Tj. Solved by fixed-point iteration.

The defaults describe the 4-channel board with BTT6050-1ERA in a vented, 3D-printed
DIN enclosure with the PCB standing vertically. R_box and RthJA are estimates for that
layout, not measurements -- replace them with measured values when a prototype exists.

Examples:
  python3 tools/heat_budget.py                      # 4 ch, 40 C, 2 oz
  python3 tools/heat_budget.py --channels 2 --r-box 0.9
  python3 tools/heat_budget.py --ambient 50 --rth-ja 50   # 1 oz copper, hot cabinet
"""
import argparse

PARTS = {
    # name: (Rds(on) at 25 C, Rds(on) at 150 C) in ohm, from datasheet max values / estimates
    'BTT6050-1ERA': (0.060, 0.105),
    'BTT6030-1ERA': (0.040, 0.070),
    'BTT6010-1ERA': (0.012, 0.022),
    'TPS27S100': (0.100, 0.166),
}


def solve(channels, amps, ambient, r_box, rth_ja, part, p_other, r_path):
    r25, r150 = PARTS[part]
    tj = ambient
    for _ in range(500):
        rds = r25 + (r150 - r25) * (tj - 25) / 125
        p_ch = amps * amps * rds
        p_tot = channels * p_ch + p_other + (channels * amps) ** 2 * r_path
        t_in = ambient + p_tot * r_box
        tj = t_in + p_ch * rth_ja
        if tj > 400:
            break
    return p_ch, p_tot, t_in, tj


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--channels', type=int, default=4)
    ap.add_argument('--part', choices=PARTS, default='BTT6050-1ERA')
    ap.add_argument('--ambient', type=float, default=40.0, help='air around the enclosure [C]')
    ap.add_argument('--r-box', type=float, default=0.6, help='enclosure air rise per watt [K/W]')
    ap.add_argument('--rth-ja', type=float, default=40.0, help='switch junction to enclosure air [K/W] (2 oz ~40, 1 oz ~50)')
    ap.add_argument('--p-other', type=float, default=0.6, help='ESP32, regulator, LEDs [W]')
    ap.add_argument('--r-path', type=float, default=0.004, help='shared supply path resistance [ohm]')
    ap.add_argument('--tj-max', type=float, default=125.0)
    ap.add_argument('--currents', default='1,2,2.5,3,3.5,4,4.5,5')
    a = ap.parse_args()
    print(f'{a.channels} x {a.part}, ambient {a.ambient:g} C, R_box {a.r_box:g} K/W, RthJA {a.rth_ja:g} K/W')
    print('  I/ch [A]  P/ch [W]  P_tot [W]  T_inside [C]  Tj [C]')
    for amps in (float(x) for x in a.currents.split(',')):
        p, pt, tin, tj = solve(a.channels, amps, a.ambient, a.r_box, a.rth_ja, a.part, a.p_other, a.r_path)
        flag = 'OVER' if tj > a.tj_max else 'marginal' if tj > a.tj_max - 15 else ''
        tj_s = f'{tj:6.0f}' if tj < 400 else '  >400'
        print(f'  {amps:8.1f}  {p:8.2f}  {pt:9.2f}  {tin:12.1f}  {tj_s}  {flag}')


if __name__ == '__main__':
    main()
