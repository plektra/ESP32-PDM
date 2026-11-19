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

- **RoHS: no non-compliant part found.** Nineteen parts rely on an exemption, which is allowed: 7(c)-I (lead in the
  glass/ceramic of thick-film resistors and in the ESP32 module) and 7(a) (high-melting lead solder in Q30, U6
  and, per the maker's SGS report, D4–D6 H5VL10B). The Kefa connector brass uses 6(c) (R3). The finished
  board is RoHS-compliant if the THT connectors are hand-soldered with **lead-free solder**.
- **REACH: two parts hold an SVHC above 0.1 % by the maker's own figures.** Q30 AGM601LL contains lead
  (CAS 7439-92-1), 1.111 % in the package body. U6 L78M05ABDT-TR contains lead at 0.2984 % of the part per ST's
  2014 material declaration (R2; the current version of that declaration was not readable). Lead above 0.1 % is
  likely, but not declared, in two more places: the Kefa connectors (R3) and some of the hongjiacheng diodes (R4).
  So the board carries an Art. 33 information duty and
  needs a SCIP notification if it is ever sold in the EU. This is paperwork, not a design change.
- **Evidence is thin for 21 parts.** No maker REACH statement was found for them, and 12 of them also have no RoHS
  statement of their own. The THT connectors are the main gap (the Kefa brass holds 3.5 % lead under exemption 6(c)).
- **For the two prototype boards (decision 101) none of this blocks the order.** RoHS and REACH apply when a product
  is placed on the EU market. The value of this check is the record, plus the list of declarations to request before
  any sale.

## Counts

| RoHS evidence | Parts |
|---|---|
| Compliant, stated by Mouser or the maker (datasheet / declaration / test report) | 30 |
| Compliant by exemption (16 UNI-ROYAL resistors 7(c)-I, Q30 7(a), D4–D6 H5VL10B 7(a), U6 7(a)) | 19 |
| Only the word "ROHS" in the JLCPCB part description (JLCPCB adds it to nearly every listing) | 12 |
| Non-compliant | 0 |

| REACH evidence | Parts |
|---|---|
| Maker states no SVHC above 0.1 % (Samsung, UNI-ROYAL, Sunlord, TI, UMW, JCET, Chipanalog, Infineon) | 33 |
| Maker says "REACH compliant" with no SVHC detail (Ymin, HRO, FOJAN, APV, Espressif) | 5 |
| Maker declares an SVHC above 0.1 % (lead: AGM601LL; L78M05ABDT-TR by ST's 2014 composition figures) | 2 |
| No statement found | 21 |

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
7(a) and lists lead under REACH. **UNVERIFIED** for L78M05ABDT-TR.
*Update 2026-11-18 (browser):* ST no longer serves this declaration. The PDF and its XML return "SORRY, PAGE NOT
FOUND" (404), also from ST's own product page, which still links them. The declaration of the sister part
L78M05CDT-TR (same DPAK, ST form dated 25/03/2015) was read instead: device 290.00 mg, lead 1.324 mg in the soft
solder, "4566" ppm of the part, RoHS exemption "7a". Its REACH answer ("does not contain" SVHC) is against the list
of 17 December 2014, before lead was added, so it is out of date. DigiKey shows "ROHS3 Compliant" and "REACH
Unaffected" for U6, which does not show exemptions. U6 stays **likely, not confirmed**. *Action before any sale:*
ask ST for the current declaration (request drafted).
*Update 2026-11-20 (owner-supplied documents):* **confirmed by ST's 2014 declaration, which names this part.** ST
Materials Declaration Form "HZGR*L765AA6", version A, 2014-10-31, "MD valid for CP: L78M05ABDT-TR,L78M05CDT-TR":
device "313.30" mg, lead 0.935 mg in the soft solder, "2984" ppm of the part, RoHS exemption "7a". Its REACH answer
is against the list of 16 June 2014 and so out of date; ST's REACH letter of 20 March 2026 (253 substances) lists
"Lead in metal form RoHS exemption 7a" for "Power Devices". U6 is now counted as a part with lead above 0.1 %.
The version ST links today (HZGR*ML052B6 ver2) is still unread. *Action before any sale:* ask ST for that current
version and the SCIP number (request drafted). Details in "Owner-supplied ST documents" below.

**R3 – THT connectors J4, J5, J10, J11 (Cixi Kefa ×3, Ningbo Kangnex ×4) and J3 USB-C (HRO): no maker statement.**
The Kefa and Kangnex parts have only the JLCPCB "ROHS" text. Their drawings say copper alloy, tin plated, with no
RoHS mark and no REACH statement. HRO claims "REACH" on its website without detail (certificate image from 2018). Brass
contacts often hold up to 4 % lead under RoHS 6(c), which can push the connector over 0.1 % as an article.
*Update 2026-11-18 (browser):* the one RoHS document on the LCSC page of the Kefa plug C440882 is SGS report
NGBEC24003843404 (2024-07-17) on the brass rod "C3604" from a copper mill: lead "34974" mg/kg (3.5 %), passed under
exemption 6(c). It is a raw-material report, not a Kefa declaration, and has no REACH content. It confirms the
concern: lead above 0.1 % of the Kefa connectors is likely.
*Action before any sale:* ask Kefa, Kangnex and HRO (through LCSC or directly) for RoHS and REACH SVHC declarations.

**R4 – Small makers with no REACH statement.** hongjiacheng (9 diode/TVS parts; RoHS stated in 8 of 9 datasheets, not
for H5VL10B C7420372), FH (MLCCs C9196, C1546; their SGS SVHC reports cover resistors only), KENTO (LED C2286),
TECHFUSE (F1–F4 C70113; its datasheet cites (EU) 2015/863 and "lead free"), XKB (switches C318884). *Action before any
sale:* request declarations, or swap to a part from a maker that publishes them where a basic/preferred equivalent
exists (decision 2 still applies).
*Update 2026-11-18 (browser):* "R+O" (LCSC) is the brand of hongjiacheng (JLCPCB): the same maker. Its SGS report
CANEC26019898601 (2026-07-30, on the LCSC page of C7420372) covers a package list with DFN1006-2L, SMA, SMB, SMC,
SOD-123, SOD-323 and SOT-23. One mixed sample holds lead "26317" mg/kg, passed under exemption 7(a). The report
does not say which packages hold the lead, so lead above 0.1 % is possible in any of the 9 hongjiacheng parts.
C7420372 now counts as "by exemption". XKB (C318884) has a maker RoHS statement (2025-03-13) and SGS material
reports from 2023 (brass: lead 130 mg/kg, no 6(c)); it now counts as maker-stated. Neither maker has a REACH
statement. MMBT5551 C2145 also moves to maker-stated (CJ's SGS report CANEC26023099405, 2026-08-21, SOT-23, lead
not detected).

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
   - R2: ask ST for the current U6 declaration and SCIP number (the 2014 version is on record; ST's link to the
     current one is dead).
   - Collect declarations for R3–R5.
   - Write the board's RoHS Declaration of Conformity and technical file.
   - Make the REACH Art. 33 statement (lead in Q30 and U6, plus the Kefa connectors and the hongjiacheng diodes if
     the makers confirm it) and the SCIP notification.
3. Repeat this check after any BOM change.
   The Candidate List grows in January and June each year, so a sale-ready record needs declarations against the
   list current at that time.

## C8 (owner question, 2026-11-18)

Keep C45783. "End of Life" is only Mouser's flag for that ordering code. JLCPCB has 3.66 M in stock as a basic part.
No basic or preferred 22 µF / 25 V X5R 0805 alternative exists. If JLCPCB stock drops, use Samsung CL21A226MAYNNNE
C602037 (extended, 865 k on 2026-11-18, same series). HRE CGA0805X5R226M250MT C6119899 is another extended option,
but its DC-bias and REACH data are not checked.

## Follow-up session (2026-11-18, later the same day)

No browser was attached to the session, so pages were read with plain fetches. That limits two of the four items.

1. **R2 (U6, ST declaration): still not verified.** The declaration PDF on www.st.com timed out twice (60 s) and
   failed once more with curl (HTTP/2 error). estore.st.com opened and links the same PDF, with RoHS grade
   "Ecopack2". The verdict above is unchanged: U6 is "likely" a second part with lead above 0.1 %.
2. **LCSC product pages of the 15 "distributor listing only" parts: read for 14, no maker certificate found.**
   The compliance fields came from a summary of each page, not from verbatim text, so treat them as a pointer.
   - No RoHS, REACH or SVHC field at all: C475108 and C441238 (Kefa), the four Kangnex parts, C9196 and C1546 (FH),
     C528763 (Chipanalog).
   - "ROHS Compliant" with documents that the fetch could not reach: C440882 (Kefa plug, 1 document), C7420372
     (H5VL10B, 1), C2145 (MMBT5551, 1), C318884 (XKB switch, 6).
   - "ROHS2 Compliant", no document: C52155402 (APV).
   - C96963 (Sunlord L1): the page is not found on lcsc.com.
   - No page has a REACH or SVHC field. The Kangnex brand page claims "CE and SGS environmental testing
     certification" without a report. The Kefa brand page makes no RoHS or REACH claim.
   - C7420372 is listed under the maker name "R+O" at LCSC and "hongjiacheng" at JLCPCB.
   The counts in this report do not change: a distributor's RoHS flag is the same class of evidence as before.
3. **DigiKey: no values obtained.** The shared pcbparts quota was used up again (resets 2026-11-19 00:00 UTC), so
   the DigiKey web pages were fetched instead. Only three of the eleven parts tried have a DigiKey page:
   U6 L78M05ABDT-TR, U1 ESP32-S3-MINI-1-N8 and L1 SWPA6045S8R2MT. On all three the "Environmental & Export
   Classifications" heading came back without its values (the table is probably filled in by script; not
   verified), and no environmental document is linked. DigiKey does not list GZ2012D601TF, VKMD1001J101MV,
   TS-1187A-B-A-B, TYPE-C-31-M-12, CA-IS3050G, AGM601LL, FRM252WJR200TK or mSMD050-60V, so it cannot cover most of
   R4/R5.
4. **Declaration requests: drafted, not sent**, in `2026-11-18-rohs-reach-requests-pdm-4ch.md` (16 makers, R3–R5).

## Browser session (2026-11-18, Chrome)

Everything below was read from the screen in Chrome. Full quotes and URLs are in the CSV notes.

1. **R2 (U6, ST declaration): not available, U6 still not verified.** Both files that ST links for L78M05ABDT-TR
   (`..._hzgr-wspc-ml052b6_ver2_signed.pdf` and `..._ver2.xml`) return ST's "404 Error Page", four tries, also from
   the "Quality & Reliability" table of https://www.st.com/en/power-management/l78m.html (which shows "Ecopack2").
   Read instead, as the closest comparable: ST "Materials Declaration Form" (IPC 1752, version 2) for
   L78M05CDT-TR / L78M05ACDT-TR, item "ZHGR*LM05AB6", site SH1A, dated 25/03/2015
   (https://www.st.com/resource/en/material_declaration/md_gr-wspc-to-252-wspc-dpak_zhgrlm05ab6.pdf):

   | Field | Value |
   |---|---|
   | Device mass | "290.00" mg |
   | Lead (CAS 7439-92-1), only entry | Soft solder (1.387 mg): 1.324 mg, "954578" ppm of the solder, "4566" ppm of the part |
   | RoHS | "meets EU RoHS requirements by application of the selected exemption(s)" = true; exemption "7a" |
   | REACH | "does not contain REACH Substances Of Very High Concern above the limits" = true |
   | Candidate List version | "REACH-17th December 2014" (lead was added in 2018) |

   This is another part number and another declaration code than U6 (HZGR*ML052B6, copper wire), so it is an
   indication only. No verdict or count changes for U6.
2. **LCSC documents: all four read; C96963 is not listed at LCSC.**

   | Part | Document | Result | Scope |
   |---|---|---|---|
   | C440882 Kefa plug | SGS NGBEC24003843404, 2024-07-17, client 浙江鸿越铜业有限公司 | Pb "34974" mg/kg, exemption 6(c); Cd "7" mg/kg; pass | Brass rod C3604 from a copper mill. Not the part, not a Kefa declaration |
   | C7420372 H5VL10B | SGS CANEC26019898601, Jul 30, 2026, client Zhuhai Hong Jia Cheng Technology | Pb "26317" mg/kg, exemption 7(a); Cd "6" mg/kg; "Pass" | One mixed "Rectifier Diode" sample for a package list that includes DFN1006-2L |
   | C2145 MMBT5551 | SGS CANEC26023099405, 2026-08-21, client 江苏长晶科技股份有限公司 | All ten substances ND; pass; no exemption | Sample type "SOT-23", with a package list |
   | C318884 XKB switch | Maker statement "ROHS 10 项声明", 东莞市星坤电子科技有限公司, 2025.03.13 | All products meet "ROHS 2.0" | All products; no exemption named |
   | C318884 | SGS SZXPC23001911605 (Brass) and SZXPC23001911609 (Gold plating), Aug 23, 2023; SZXPC23001911107 (PA66), Aug 21, 2023 | Pb "130", "42" and "5" mg/kg; "Pass" | Materials. The two metal reports test Cd, Pb, Hg and Cr(VI) only |
   | C318884 | Two .zip archives (轻触开关原材料, 全量物料通用原材料) | **Not opened** (download only) | – |

   None of these documents covers REACH. C7420372: "R+O" is hongjiacheng's brand (the LCSC file name reads
   "R+O(宏嘉诚)" and the SGS client is Zhuhai Hong Jia Cheng), so both names are right. C96963: the LCSC product
   page shows "Part not found" and the search for SWPA6045S8R2MT returns no results.
3. **DigiKey "Environmental & Export Classifications".**

   | Part | RoHS Status | REACH Status |
   |---|---|---|
   | U6 L78M05ABDT-TR | "ROHS3 Compliant" | "REACH Unaffected" |
   | U1 ESP32-S3-MINI-1-N8 | no such row | "REACH Unaffected" |
   | L1 SWPA6045S8R2MT | no such row | no such row |

   A distributor flag does not show exemptions or the Candidate List version, so no count changes from these.
4. **Counts changed** (RoHS table only): maker-stated 28 → 30 (C2145, C318884), by exemption 18 → 19 (C7420372),
   listing only 15 → 12. The REACH table is unchanged.
5. **Request drafts corrected** (still not sent): Kefa, hongjiacheng and XKB now refer to the documents that
   exist; a request to ST for the U6 declaration is added.

## Owner-supplied ST documents (2026-11-20)

The owner found two ST documents on a distributor's document host and one on Mouser. All three were read (text
extracted with pypdf; the Mouser one is a scan and was read from a rendering); nothing is copied into the repo.

1. **ST Materials Declaration Form for U6** (IPC 1752, version 2), 4 pages:
   https://4donline.ihs.com/images/VipMasterIC/IC/SGST/SGST-E-A0002296617/SGST-E-A0002857088-1.pdf?hkey=6D0214268300F1406B835FE51CB13195

   | Field | Value as written |
   |---|---|
   | Mfr Item Name / version / site / date | "HZGR*L765AA6" / "A" / "SH1A" / "2014-10-31" |
   | Scope | "TO-252 DPAK Cu Wire; MD valid for CP: L78M05ABDT-TR,L78M05CDT-TR." |
   | Device mass | "313.30" mg, "ECOPACK® 2" |
   | Lead (CAS 7439-92-1), only entry | "Soft solder" (0.979 mg): 0.935 mg, "955056" ppm in the material, "2984" ppm in the product |
   | RoHS ("ROHS directive 2011/65/EU _ July 2011") | "Product(s) meets EU RoHS requirements by application of the selected exemption(s)" = true; exemption "7a" |
   | REACH SVHC | "The product does not contain REACH Substances Of Very High Concern above the limits" = true |
   | Candidate List version | "REACH-16th June 2014" (lead was added in 2018) |

   This names U6, so R2 is confirmed as far as a 2014 document can: lead 0.2984 % of the part, under 7(a). It is
   version A of another declaration code than the one ST links today (HZGR*ML052B6 ver2, still 404), so the
   figures of current production are **not verified**.
2. **ST "REACH Communication to Customers"**, Geneva, March 20th 2026, 2 pages, company-wide, marked "ST
   Restricted" (so cited by title and date only). It covers the EU Candidate List "through Feb 4th 2026 …
   containing 253 substances". ST products "do not contain SVHC candidate substances, except for some articles";
   the exception table has "Power Devices – Lead in metal form RoHS exemption 7a / ELV exemption 8e", and
   "When relevant, ST products are reported on the SCIP database." It names no part number and does not say
   whether a DPAK regulator is a "Power Device".
3. **ST letter "STMicroelectronics semiconductor products RoHS compliance"**, Geneva, July 22nd, 2019, one scanned
   page signed by two ST vice presidents: https://www.mouser.com/catalog/additional/STMicroelectronics_5113_RoHS_Certificate.pdf
   (Mouser refuses scripted downloads; the owner downloaded it and it was read from a rendering of the page.)
   ST "Ecopack semiconductor products" "are compliant with … RoHS Directive (… 2011/65/EU and former 2002/95/EC
   as amended by 2015/863/EU)" and "do not contain any of the restricted substances except Lead (Pb) that may be
   used according to the exemptions given under RoHS Annex III (7a, 7cI,15)". Company-wide, no part numbers. U6
   is an "ECOPACK® 2" part, so this covers the four phthalates of (EU) 2015/863, which the 2014 declaration
   could not.
4. **Counts changed** (REACH table only): maker declares an SVHC 1 → 2 (U6), no statement 22 → 21. U6 was already
   counted under "by exemption" in the RoHS table; the exemption is now named.

## Still open

1. R2: the current ST declaration for U6 L78M05ABDT-TR (HZGR*ML052B6 ver2) is not published at the moment (404);
   the 2014 version is on record. Before a sale, try the link again or send the drafted request to ST:
   https://www.st.com/resource/en/material_declaration/md_gr-wspc-to-wspc-252-wspc-dpak-wspc-cu-wspc-wire_hzgr-wspc-ml052b6_ver2_signed.pdf
2. The two .zip archives on the LCSC page of C318884 were not opened.
3. Owner: send the drafted requests through LCSC support (ST: its own support page) when a sale is planned.
4. Later: the same check for pdm-hc2 once its BOM is settled.
