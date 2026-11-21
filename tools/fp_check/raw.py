import json, sys
kic = json.load(open(sys.argv[1]))
easy = json.load(open(sys.argv[2]))
for ref, code in (a.split('=') for a in sys.argv[3:]):
    print(f'## {ref} {code} KiCad fp {kic[ref]["fp"]} rot {kic[ref]["rot"]}')
    for p in kic[ref]['pads']:
        if p['n'] == '' and p['w'] < 1.0:
            continue
        print(f'  K {p["n"]:>4} ({p["x"]:+.3f},{p["y"]:+.3f}) {p["w"]:.2f}x{p["h"]:.2f} r{p["rot"]} drill {p["drill"]} {p["net"][:18]}')
    fp = easy[code]['footprint']
    print(f'  EasyEDA {fp["name"]} src {fp.get("source_link")}')
    names = {str(p['number']): p.get('name') for p in easy[code].get('pins', [])}
    for p in fp['pads']:
        print(f'  E {str(p["number"]):>4} ({p["x"]:+.3f},{p["y"]:+.3f}) {p["size"][0]:.2f}x{p["size"][1]:.2f} '
              f'{p["layer"]} hole {p.get("hole")} name {names.get(str(p["number"]))}')
