# RoHS/REACH declaration requests – pdm-4ch (drafts, not sent)

Drafts for findings R2–R5 of `2026-11-18-rohs-reach-pdm-4ch.md`. The owner sends them through LCSC support (one
ticket per maker works best, since LCSC forwards each to a different supplier). Fill in `<name>` and
`<LCSC order no.>` before sending. Nothing here has been sent.

Not needed for the two prototype boards (decision 101). Send these when a sale in the EU is planned. The Candidate
List changes in January and June, so a declaration collected early may have to be refreshed.

## Common text

Used at the start of every request; the per-maker part follows it.

> Subject: RoHS and REACH SVHC declaration request – `<maker>` – `<LCSC part numbers>`
>
> Hello,
>
> I buy the parts listed below through LCSC / JLCPCB (order `<LCSC order no.>`) and use them in an electronic product
> that will be placed on the EU market. For its technical file I need the manufacturer's environmental documents.
> Could you please forward this request to the manufacturer, or send the documents if you already hold them?
>
> For each part number below, please provide:
>
> 1. **RoHS**: a declaration of compliance with Directive 2011/65/EU as amended by (EU) 2015/863 (10 substances),
>    naming every Annex III exemption used (for example 6(c), 7(a), 7(c)-I), or stating that none is used.
> 2. **REACH**: a declaration under Regulation (EC) 1907/2006 Article 33 against the current Candidate List
>    (253 substances, update of 4 February 2026, or later). Please state whether any SVHC is present above 0.1 % w/w
>    of the part. If one is, please give the substance name, CAS number, concentration and where in the part it is.
> 3. If available: a third-party test report (SGS, CTI or similar) or a full material declaration (IPC-1752A or a
>    material content sheet) that covers this part number or its series.
>
> A signed and dated PDF on the manufacturer's letterhead is enough. A statement that covers the whole series is
> fine if it names the series.
>
> Thank you,
> `<name>`

## R3 – connectors

### Cixi Kefa Elec

> Parts: C475108 KF135T-10.16-2P, C441238 KF2EDGRC-5.08-4P, C440882 KF2EDGK-5.08-4P-AA.
>
> The drawings give the contact material as copper alloy, tin plated. Please state the lead content of the contact
> and screw alloys, and whether RoHS exemption 6(c) (copper alloy with up to 4 % lead) is used. If it is, lead is
> likely above 0.1 % of the part, so please confirm this in the REACH statement.
>
> The RoHS document on the LCSC page of C440882 is SGS report NGBEC24003843404 (2024-07-17) on the brass rod C3604:
> lead 34974 mg/kg under exemption 6(c). Please confirm that this brass is used in the three parts above, and give
> the lead content as a share of each whole part (needed for the REACH Article 33 statement).

### Ningbo Kangnex Elec

> Parts: C26895 WJ15EDGRC-3.81-10P-14-00A, C26865 WJ15EDGK-3.81-10P-14-00A, C7245 WJ15EDGRC-3.81-04P-14-00A,
> C7244 WJ15EDGK-3.81-04P-14-00A.
>
> The drawings give the contact material as copper alloy, tin plated. Please state the lead content of the contact
> and screw alloys, and whether RoHS exemption 6(c) (copper alloy with up to 4 % lead) is used. If it is, lead is
> likely above 0.1 % of the part, so please confirm this in the REACH statement.
>
> The LCSC brand page says the products "have passed CE and SGS environmental testing certification". Please send
> the SGS report(s) that cover the 15EDG 3.81 mm series.

### Korean Hroparts Elec (HRO)

> Part: C165948 TYPE-C-31-M-12.
>
> The drawing carries a RoHS stamp and the maker's website states RoHS and REACH compliance, but without a document
> or a Candidate List version. Please send a dated declaration, and state whether the contact or shell alloy uses
> RoHS exemption 6(c).

## R4 – makers with no REACH statement

### hongjiacheng (Zhuhai Hongjiacheng Technology; brand "R+O" at LCSC)

> Parts: C19077548 SMAJ30CA, C19077539 SMAJ18CA, C19077607 SMCJ30CA, C42371557 SMDJ40CA, C22466351 DSK16,
> C22466350 BAT54C, C7420333 BAT54S, C19077396 BZT52C3V3, C7420372 H5VL10B.
>
> The datasheets state "RoHS compliant, halogen free" for all of these except H5VL10B (C7420372), which has no RoHS
> statement. Please include it explicitly.
>
> SGS report CANEC26019898601 (2026-07-30, on the LCSC page of C7420372) tests one mixed sample for the whole package
> list and finds lead 26317 mg/kg under exemption 7(a). Please state for each part number above whether
> high-melting lead solder (exemption 7(a)) is used, and if so the lead content as a share of the whole part.
> The report does not cover REACH, so the REACH declaration is still needed.

### FH (Guangdong Fenghua Advanced Technology)

> Parts: C9196 1206B102K202NT (MLCC 1 nF 2 kV X7R 1206), C1546 0402CG101J500NT (MLCC 100 pF 50 V C0G 0402).
>
> Fenghua publishes SGS SVHC reports for chip resistors only. Please send the equivalent report or declaration for
> multilayer ceramic capacitors.

### Hubei KENTO Elec

> Part: C2286 KT-0603R (red LED 0603). The datasheet says "Meet ROHS, Green Product" only.

### TECHFUSE

> Part: C70113 mSMD050-60V (resettable fuse 1812). The datasheet cites 2015/863/EU and "lead free device", with no
> REACH statement.

### XKB Connection

> Part: C318884 TS-1187A-B-A-B (tactile switch).
>
> The LCSC page carries the maker's RoHS statement of 2025-03-13 and SGS material reports from 2023 (brass, gold
> plating, PA66). They do not cover REACH and name no exemption. Please send a REACH SVHC declaration, and confirm
> that no RoHS exemption (for example 6(c)) is used in this part.

## R5 – statements to refresh or complete

### Ymin (Shanghai Yongming)

> Part: C487384 VKMD1001J101MV (aluminium electrolytic capacitor 100 µF 100 V).
>
> The datasheet states RoHS compliance and a public statement says the products meet REACH, with no SVHC detail.
> Please send a REACH SVHC declaration that names the Candidate List version.

### FOJAN

> Part: C7420022 FRM252WJR200TK (alloy current-sense resistor 0.2 Ω 2512).
>
> FOJAN's published CTI SVHC report covers thick-film chip resistors. Please send a report or declaration that
> covers the FRM alloy series.

### APV Technologies

> Part: C52155402 ANTC1608-103F3380FB (NTC thermistor 10 kΩ 0603).
>
> The datasheet revision of 2025-01-08 carries the marks "RoHS, REACH, SVHC-Free, Halogen Free". The revision of
> 2026-06-21 does not. Please confirm that the part still meets them, and state whether RoHS exemption 7(c)-I (lead
> in glass or ceramic) is used.

### Sunlord

> Parts: C1017 GZ2012D601TF (ferrite bead), C96963 SWPA6045S8R2MT (power inductor 8.2 µH).
>
> Sunlord's published declaration is dated 2020-03-18 and covers 205 SVHC. Please send the current version.

### Chipanalog

> Part: C528763 CA-IS3050G (isolated CAN transceiver).
>
> Chipanalog's REACH declaration is dated 2024-11-07 and covers 242 SVHC. Please send the current version, and a
> RoHS declaration that names any exemption used (none is stated in the datasheet).

### AGM-Semi

> Part: C5464765 AGM601LL (N-MOSFET, TOLL package).
>
> The published SGS reports (RoHS CANEC25003064001, REACH CANEC25003088301, March 2025) test a TO252-2L sample
> against 247 SVHC and find lead above 0.1 % under RoHS exemption 7(a). Please send a report or declaration for
> the TOLL package against the current Candidate List, with the lead concentration as a share of the whole part.
> This figure is needed for the Article 33 statement and the SCIP notification.

### Espressif Systems

Espressif is better asked directly (sales or technical inquiry form on espressif.com) than through LCSC.

> Part: C2913206 ESP32-S3-MINI-1-N8.
>
> The Environmental Compliance Declaration of 2026-05-15 states "REACH SVHC 253" and RoHS with exemption 7(c)-I.
> Please send the module's material declaration or test report, and state whether any component inside the module
> holds an SVHC (for example lead) above 0.1 % w/w of that component, since Article 33 counts each component as an
> article (EU Court of Justice C-106/14).

## Not requested through LCSC

- **Samsung, UNI-ROYAL, TI, UMW, JCET, Infineon:** current statements are already on file in the CSV.

### STMicroelectronics (U6, R2)

Ask ST directly (online support on st.com), not through LCSC.

> Part: L78M05ABDT-TR (DPAK).
>
> The material declaration linked from the product page (Quality & Reliability, "Material Declaration", file
> `md_gr-wspc-to-wspc-252-wspc-dpak-wspc-cu-wspc-wire_hzgr-wspc-ml052b6_ver2_signed.pdf`) returns "page not found",
> as does its XML version. Please send the current IPC-1752 material declaration for this part, with the RoHS
> exemption used (7(a)?), the lead content in ppm of the part, and the REACH SVHC answer against the current
> Candidate List.
