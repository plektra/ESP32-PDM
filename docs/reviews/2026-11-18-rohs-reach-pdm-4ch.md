# RoHS and REACH check – pdm-4ch (2026-11-18)

Scope: the 54 BOM lines of `hardware/pdm-4ch/fab/ESP32-PDM-4CH-bom-jlc.csv` and the 7 hand-bought THT connector
parts (J10 KF135T C475108, which has no plug; J11 C441238 + C440882; J5 C26895 + C26865; J4 C7245 + C7244). That makes
61 parts. Per-part data, sources and links: `2026-11-18-rohs-reach-pdm-4ch.csv` (next to this file).

Not checked: the DNP positions (FL1 C20624726, L2, C22, R73 and the other unfitted parts; L2 is the same part as L1
C96963, so its result carries over). Also not checked: the PCB, which is ordered as HASL lead-free (board file
`copper_finish "HAL lead-free"`, `fab/README.md`), and the solder used by hand on the THT connectors.

Basis: RoHS = Directive 2011/65/EU as amended by (EU) 2015/863 (10 substances, 0.1 % per homogeneous material, Cd
0.01 %). REACH = Regulation (EC) 1907/2006, Art. 33: an SVHC from the Candidate List above 0.1 % w/w per article,
counted per component (EU Court of Justice C-106/14, 2015). The Candidate List had 253 entries at the date of this
check (latest update 2026-02-04 in the sources found).

Method: maker and part from JLCPCB. RoHS status from Mouser's flag, else from the maker's datasheet or declaration,
else from the JLCPCB listing text. REACH from maker declarations and SGS/CTI test reports on the makers' sites.
DigiKey could not be used (shared daily quota used up). No document was invented; where nothing was found, the CSV
says so.

## Verdict

- **RoHS: no non-compliant part found.** Seventeen parts rely on an exemption, which is allowed: 7(c)-I (lead in the
  glass/ceramic of thick-film resistors and in the ESP32 module) and 7(a) (high-melting lead solder in Q30, likely
  also U6). The finished board is RoHS-compliant if the THT connectors are hand-soldered with **lead-free solder**.
- **REACH: one part declares an SVHC above 0.1 %.** Q30 AGM601LL contains lead (CAS 7439-92-1), 1.111 % in the
  package body. U6 L78M05ABDT-TR is likely a second (not confirmed). So the board carries an Art. 33 information
  duty and needs a SCIP notification if it is ever sold in the EU. This is paperwork, not a design change.
- **Evidence is thin for 22 parts.** No maker REACH statement was found for them, and 15 of them also have no RoHS
  statement of their own. The THT connectors are the main gap (brass contacts can hold lead under exemption 6(c)).
- **For the two prototype boards (decision 101) none of this blocks the order.** RoHS and REACH apply when a product
  is placed on the EU market. The value of this check is the record, plus the list of declarations to request before
  any sale.

## Counts

| RoHS evidence | Parts |
|---|---|
| Compliant, stated by Mouser or the maker (datasheet / declaration) | 28 |
| Compliant by exemption (16 UNI-ROYAL resistors 7(c)-I, Q30 7(a), U6 exemption not named) | 18 |
| Only the word "ROHS" in the JLCPCB part description (JLCPCB adds it to nearly every listing) | 15 |
| Non-compliant | 0 |

| REACH evidence | Parts |
|---|---|
| Maker states no SVHC above 0.1 % (Samsung, UNI-ROYAL, Sunlord, TI, UMW, JCET, Chipanalog, Infineon) | 33 |
| Maker says "REACH compliant" with no SVHC detail (Ymin, HRO, FOJAN, APV, Espressif) | 5 |
| Maker declares an SVHC above 0.1 % (AGM601LL, lead) | 1 |
| No statement found | 22 |

## Findings

**R1 – Q30 AGM601LL (C5464765) contains lead above 0.1 % (REACH SVHC).** SGS report CANEC25003088301, 2025-03-06,
p. 2–3: "the results of 247 SVHC in the Candidate List are > 0.1% (w/w) in the articles of the submitted sample";
test result 001: lead 7439-92-1, 1.111 % in the black body. RoHS: SGS report CANEC25003064001 (2025-03-04, p. 4)
measures 30204 mg/kg Pb in one part under exemption 7(a). Both are on agm-mos.com (lists/46.html, lists/45.html).
Limits of this evidence: the sample is a TO252-2L, and TOLL (the AGM601LL package) is named only in the client's
package list. The report checks against 247 substances, not the current 253. Lead in the high-melting die-attach
solder is normal for power MOSFET packages, and the Infineon IPT007N06N that Q30 replaced would likely be similar
(not checked).
*Effect:* if sold in the EU, the board must come with information that it contains lead in Q30 (Art. 33(1)), and the
board needs a SCIP database entry. No change for the prototypes. Replacing Q30 only for this reason is not proposed.

**R2 – U6 L78M05ABDT-TR (C58069): exemption and SVHC not confirmed.** Mouser lists it as "RoHS compliant by
exemption"; ST's page shows ECOPACK2 and links an IPC-1752 material declaration, but st.com could not be read from
here. A comparable ST DPAK declaration (ACST1220H-8BTR, 2023) declares about 1.2 % lead in die-attach solder under
7(a) and lists lead under REACH. **UNVERIFIED** for L78M05ABDT-TR. *Action:* download the declaration in a browser
(URL in the CSV) and record the result.

**R3 – THT connectors J4, J5, J10, J11 (Cixi Kefa ×3, Ningbo Kangnex ×4) and J3 USB-C (HRO): no maker statement.**
The Kefa and Kangnex parts have only the JLCPCB "ROHS" text. Their drawings say copper alloy, tin plated, with no
RoHS mark and no REACH statement. HRO claims "REACH" on its website without detail (certificate image from 2018). Brass
contacts often hold up to 4 % lead under RoHS 6(c), which can push the connector over 0.1 % as an article.
*Action before any sale:* ask Kefa, Kangnex and HRO (through LCSC or directly) for RoHS and REACH SVHC declarations.

**R4 – Small makers with no REACH statement.** hongjiacheng (9 diode/TVS parts; RoHS stated in 8 of 9 datasheets, not
for H5VL10B C7420372), FH (MLCCs C9196, C1546; their SGS SVHC reports cover resistors only), KENTO (LED C2286),
TECHFUSE (F1–F4 C70113; its datasheet cites (EU) 2015/863 and "lead free"), XKB (switches C318884). *Action before any
sale:* request declarations, or swap to a part from a maker that publishes them where a basic/preferred equivalent
exists (decision 2 still applies).

**R5 – Statements without SVHC detail, or based on an old list.** Ymin (C31), FOJAN (R54–R56; their SVHC report covers
thick-film resistors, not the FRM alloy series), APV (TH1; the 2026 datasheet revision dropped the "SVHC-Free" mark),
Espressif (U1; declaration 2026-05-15 claims "REACH SVHC 253" with no detail and names RoHS 7(c)-I). Lists that are out
of date: Sunlord (205 substances, 2020), Chipanalog (242, 2024), AGM (247, 2025). *Action before any sale:* refresh
these declarations.

**R6 – UNI-ROYAL resistors (16 parts): lead present, but not counted as an SVHC.** The maker's statement
URM-MSG-20260105 names RoHS 7(c)-I. SGS report CANEC25000533033 (2025-11-24, 251 substances) finds lead but marks it
"NA^", meaning lead bound in glass is not counted as the SVHC; TI's REACH statement SZZQ087 takes the same view of
7(c)-I. Recorded as "no SVHC" on that basis.

**Minor.** C45783 (Samsung CL21A226MAQNNNE, C8) is "End of Life" at Mouser: check stock and an alternative before the
next order. C2145 MMBT5551 is plain SOT-23 (JLCPCB), so the lead-free JCET SOT-23 report applies. That maker's
leaded report covers "K" packages only.

## For the pre-order / sale checklist

1. Prototypes (decision 101): nothing to do except hand-solder J4, J5, J10, J11 with lead-free solder (e.g. SAC305 or
   Sn99.3Cu0.7) if the boards are to stay RoHS-compliant.
2. Before any sale in the EU (also under CE marking, together with the EMC and LVD work):
   - Settle R2 (ST declaration).
   - Collect declarations for R3–R5.
   - Write the board's RoHS Declaration of Conformity and technical file.
   - Make the REACH Art. 33 statement (lead in Q30, plus U6 if R2 confirms it) and the SCIP notification.
3. Repeat this check after any BOM change.
   The Candidate List grows in January and June each year, so a sale-ready record needs declarations against the
   list current at that time.

## C8 (owner question, 2026-11-18)

Keep C45783. "End of Life" is only Mouser's flag for that ordering code. JLCPCB has 3.66 M in stock as a basic part.
No basic or preferred 22 µF / 25 V X5R 0805 alternative exists. If JLCPCB stock drops, use Samsung CL21A226MAYNNNE
C602037 (extended, 865 k on 2026-11-18, same series). HRE CGA0805X5R226M250MT C6119899 is another extended option,
but its DC-bias and REACH data are not checked.

## Follow-up (a session with a browser, `claude --chrome`)

1. R2: open the ST material declaration for U6 L78M05ABDT-TR and read the lead content, the RoHS exemption and the
   REACH SVHC entry:
   https://www.st.com/resource/en/material_declaration/md_gr-wspc-to-wspc-252-wspc-dpak-wspc-cu-wspc-wire_hzgr-wspc-ml052b6_ver2_signed.pdf
   (product page https://estore.st.com/en/l78m05abdt-tr-cpn.html). Update R2 and the C58069 row of the CSV.
2. Read the RoHS field on the LCSC product pages of the 15 parts that rely only on the JLCPCB listing (the CSV
   `rohs_status` says "distributor listing only"). Look for any maker certificate linked there, especially for the
   Kefa/Kangnex connectors (R3).
3. DigiKey (the pcbparts quota resets at 00:00 UTC daily): RoHS and REACH status for the parts DigiKey stocks, mainly
   to cover R4/R5.
4. Draft (not send) the declaration requests to the makers in R3–R5. The owner sends them through LCSC support.
5. Later: the same check for pdm-hc2 once its BOM is settled.
