"""
Supply chain relationships for Indian stocks.
~100 hand-curated relationships across 13 sectors.

Format: (supplier, customer, weight, note)
  weight 0.5+ = highly exposed (customer dominates supplier's book)
  weight 0.2-0.5 = meaningfully exposed
  weight 0.05-0.2 = relevant but not dominant
  weight <0.05 = trivial, usually excluded

These are APPROXIMATIONS from annual reports, concalls, brokerage notes.
The validation step (validate_relationship in supply_chain_analytics.py)
checks whether actual price correlation supports each claimed link.
"""

SUPPLY_CHAIN = [
    # ============ AUTO ECOSYSTEM ============
    # Maruti Suzuki — India's largest PV OEM
    ("BHARATFORG.NS",  "MARUTI.NS",     0.10, "Forgings for engine/chassis"),
    ("MOTHERSON.NS",   "MARUTI.NS",     0.20, "Wiring harnesses, mirrors, polymer parts"),
    ("BOSCHLTD.NS",    "MARUTI.NS",     0.25, "Fuel injection, electronics, brakes"),
    ("SUBROS.NS",      "MARUTI.NS",     0.65, "Subros is heavily Maruti-dependent for AC systems"),
    ("SONACOMS.NS",    "MARUTI.NS",     0.15, "Driveline components"),
    ("MRF.NS",         "MARUTI.NS",     0.10, "OEM tyre supply"),
    ("APOLLOTYRE.NS",  "MARUTI.NS",     0.10, "OEM tyre supply"),


    # Mahindra
    ("BHARATFORG.NS",  "M&M.NS",        0.08, "Heavy forgings for SUVs/tractors"),
    ("MOTHERSON.NS",   "M&M.NS",        0.10, "Interior/exterior components"),
    ("BOSCHLTD.NS",    "M&M.NS",        0.15, "Diesel and electronics"),

    # ============ STEEL DOWNSTREAM ============
    # Steel producers → metal-buying customers
    ("TATASTEEL.NS",   "MARUTI.NS",     0.03, "Auto-grade steel"),
    ("TATASTEEL.NS",   "LT.NS",         0.04, "Structural steel for infra"),
    ("TATASTEEL.NS",   "BHEL.NS",       0.03, "Plant equipment steel"),
    ("JSWSTEEL.NS",    "LT.NS",         0.04, "Structural steel"),
    ("JSWSTEEL.NS",    "MARUTI.NS",     0.03, "Auto-grade steel"),
    ("JSWSTEEL.NS",    "SIEMENS.NS",    0.02, "Steel for electrical equipment"),
    ("SAIL.NS",        "LT.NS",         0.06, "Govt infra projects"),
    ("SAIL.NS",        "BHEL.NS",       0.04, "Power equipment plant"),
    ("SAIL.NS",        "KEC.NS",        0.03, "Transmission tower steel"),
    ("SAIL.NS",        "KPIL.NS",       0.03, "Tower steel"),

    # ============ ALUMINUM DOWNSTREAM ============
    ("HINDALCO.NS",    "MARUTI.NS",     0.03, "Auto-grade aluminum"),
    ("HINDALCO.NS",    "SIEMENS.NS",    0.02, "Aluminum for electrical equipment"),
    ("HINDALCO.NS",    "ABB.NS",        0.02, "Aluminum for electrical equipment"),
    ("NATIONALUM.NS",  "MARUTI.NS",     0.02, "Auto-grade aluminum"),
    ("NATIONALUM.NS",  "BHEL.NS",       0.02, "Power equipment"),

    # ============ COPPER DOWNSTREAM (via cable companies) ============
    # Cable cos are the price-takers on copper; they sell to T&D / infra / construction
    ("POLYCAB.NS",     "LT.NS",         0.05, "Power cables for L&T infra projects"),
    ("KEI.NS",         "LT.NS",         0.05, "Cables for infra"),
    ("HAVELLS.NS",     "LT.NS",         0.04, "Switchgear, cables"),
    ("POLYCAB.NS",     "BHEL.NS",       0.03, "Cables for power equipment"),
    ("KEI.NS",         "KEC.NS",        0.04, "Cables for transmission projects"),
    ("KEI.NS",         "KPIL.NS",       0.04, "Cables for tower projects"),

    # ============ TELECOM ECOSYSTEM ============
    ("INDUSTOWER.NS",  "BHARTIARTL.NS", 0.45, "Indus' largest tenant is Airtel"),
    ("INDUSTOWER.NS",  "RELIANCE.NS",   0.30, "Jio under Reliance, major tenant via shared infra"),
    ("HFCL.NS",        "BHARTIARTL.NS", 0.20, "Fiber for Airtel rollout"),
    ("HFCL.NS",        "RELIANCE.NS",   0.15, "Fiber for Jio"),

    # ============ REFINERS → AVIATION / DOWNSTREAM ============
    ("BPCL.NS",        "INDIGO.NS",     0.05, "Aviation fuel"),
    ("HINDPETRO.NS",   "INDIGO.NS",     0.05, "Aviation fuel"),
    ("IOC.NS",         "INDIGO.NS",     0.05, "Aviation fuel"),

    # ============ ONGC → REFINERS ============
    ("ONGC.NS",        "IOC.NS",        0.20, "Domestic crude supply"),
    ("ONGC.NS",        "BPCL.NS",       0.15, "Domestic crude supply"),
    ("ONGC.NS",        "HINDPETRO.NS",  0.12, "Domestic crude supply"),
    ("ONGC.NS",        "RELIANCE.NS",   0.10, "Crude feedstock"),
    ("GAIL.NS",        "PETRONET.NS",   0.10, "Gas transmission/infra interconnect"),

    # ============ SUGAR ECOSYSTEM ============
    # Sugar mills → ethanol blending (OMCs) AND → FMCG (sugar buyers)
    ("BALRAMCHIN.NS",  "IOC.NS",        0.15, "Ethanol blending for petrol"),
    ("BALRAMCHIN.NS",  "BPCL.NS",       0.10, "Ethanol blending"),
    ("BALRAMCHIN.NS",  "HINDPETRO.NS",  0.10, "Ethanol blending"),
    ("TRIVENI.NS",     "IOC.NS",        0.10, "Ethanol blending"),
    # Sugar → FMCG (sugar is a major input)
    ("BALRAMCHIN.NS",  "NESTLEIND.NS",  0.03, "Sugar input for confectionery/dairy"),
    ("BALRAMCHIN.NS",  "BRITANNIA.NS",  0.05, "Sugar input for biscuits"),
    ("DHAMPURSUG.NS",  "BRITANNIA.NS",  0.04, "Sugar input"),

    # ============ CEMENT ECOSYSTEM ============
    # Cement → infra and construction (LT primarily, BHEL plants, capital goods)
    ("ULTRACEMCO.NS",  "LT.NS",         0.06, "Major cement supplier for L&T projects"),
    ("SHREECEM.NS",    "LT.NS",         0.04, "Cement for north India infra"),
    ("AMBUJACEM.NS",   "LT.NS",         0.05, "Adani-group cement supplier to infra"),
    ("ACC.NS",         "LT.NS",         0.04, "Cement"),
    ("DALBHARAT.NS",   "LT.NS",         0.03, "South/east cement"),

    # ============ SPECIALTY CHEMICALS ECOSYSTEM ============
    # Specialty chem → paints (raw material supply)
    ("SRF.NS",         "ASIANPAINT.NS", 0.05, "Refrigerant gases, specialty intermediates"),
    ("AARTIIND.NS",    "ASIANPAINT.NS", 0.04, "Pigment intermediates"),
    ("AARTIIND.NS",    "BERGEPAINT.NS", 0.04, "Pigment intermediates"),
    ("DEEPAKNTR.NS",   "ASIANPAINT.NS", 0.05, "Nitric acid, intermediates"),
    ("DEEPAKNTR.NS",   "BERGEPAINT.NS", 0.04, "Intermediates"),
    # Fertilizers → no clean listed downstream in our universe (farmers, agri stocks not yet here)

    # ============ FMCG INPUT CHAIN ============
    # Already partially covered above (sugar → FMCG)
    # Palm oil / agri inputs harder to map without commodity proxies

    # ============ IT & TECH ============
    # IT services don't have clean Indian supply chain (clients are foreign)
    # But cross-correlations via INFY/WIT ADRs handle international scan
    # No supply chain edges added — IT cos are more macro-driven

    # ============ CAPITAL GOODS INTRA-SECTOR ============
    # BHEL produces power equipment, sells to power generation cos
    # Power gen cos (NTPC, Tata Power) not in universe yet — skip for now
    # SIEMENS & ABB sell electrical equipment to infra projects
    ("SIEMENS.NS",     "LT.NS",         0.04, "Electrical systems for L&T projects"),
    ("ABB.NS",         "LT.NS",         0.04, "Electrical and automation systems"),
    ("CUMMINSIND.NS",  "LT.NS",         0.03, "Engines for construction equipment"),
    ("THERMAX.NS",     "LT.NS",         0.02, "Process equipment for infra"),

    # ============ DEFENSE & AEROSPACE ============
    # Defense ecosystem is opaque but a few known relationships:
    # HAL is the prime defense contractor; BEL provides avionics/electronics;
    # Bharat Forge has a defense division supplying components;
    # Mazagon Dock builds warships using SAIL/Tata Steel.
    ("BEL.NS",         "HAL.NS",         0.15, "Avionics, radars, electronic warfare systems"),
    ("BHARATFORG.NS",  "HAL.NS",         0.05, "Aerospace forgings, defense components"),
    ("ASTRAMICRO.NS",  "HAL.NS",         0.20, "RF and microwave subsystems for radar"),
    ("ASTRAMICRO.NS",  "BEL.NS",         0.25, "Microwave components for BEL systems"),
    ("DATAPATTNS.NS",  "BEL.NS",         0.20, "Defense electronics, ATE systems"),
    ("DATAPATTNS.NS",  "HAL.NS",         0.10, "Avionics test equipment"),
    ("TATASTEEL.NS",   "MAZDOCK.NS",     0.04, "Naval grade steel for shipbuilding"),
    ("SAIL.NS",        "MAZDOCK.NS",     0.05, "Steel plates for ship hulls"),
    ("SAIL.NS",        "COCHINSHIP.NS",  0.04, "Steel for shipbuilding"),

    # ============ POWER & UTILITIES ============
    # Power ecosystem: NTPC/Tata Power/JSW Energy are generators;
    # Power Grid transmits; T&D infra companies (KEC, KPIL) build the grid.
    ("SAIL.NS",        "POWERGRID.NS",   0.05, "Steel for transmission towers and substations"),
    ("KEC.NS",         "POWERGRID.NS",   0.20, "Transmission tower & line EPC for Power Grid"),
    ("KPIL.NS",        "POWERGRID.NS",   0.18, "T&D infrastructure projects"),
    ("POLYCAB.NS",     "POWERGRID.NS",   0.04, "Power cables for grid infra"),
    ("KEI.NS",         "POWERGRID.NS",   0.04, "Specialty cables"),
    ("BHEL.NS",        "NTPC.NS",        0.25, "Power generation equipment, boilers, turbines for NTPC plants"),
    ("BHEL.NS",        "TATAPOWER.NS",   0.10, "Power equipment for Tata Power thermal plants"),
    ("THERMAX.NS",     "NTPC.NS",        0.05, "Industrial boilers, environment systems"),
    ("CUMMINSIND.NS",  "TATAPOWER.NS",   0.03, "Backup generators for utility operations"),

    # ============ PHARMA — API & INTERMEDIATES CHAIN ============
    # Big pharma majors (Sun, Dr Reddy, Cipla, Lupin) buy APIs and intermediates from
    # specialty chemical companies and contract manufacturers.
    # Divi's Labs is the cleanest API supplier story; Aarti and Deepak Nitrite
    # provide specialty intermediates.
    ("DIVISLAB.NS",    "SUNPHARMA.NS",   0.08, "API supply to global pharma incl. Sun"),
    ("DIVISLAB.NS",    "DRREDDY.NS",     0.06, "API and intermediates"),
    ("DIVISLAB.NS",    "CIPLA.NS",       0.05, "API supply"),
    ("AARTIIND.NS",    "SUNPHARMA.NS",   0.04, "Specialty pharma intermediates"),
    ("DEEPAKNTR.NS",   "SUNPHARMA.NS",   0.03, "Phenol derivatives, pharma inputs"),
    ("NAVINFLUOR.NS",  "SUNPHARMA.NS",   0.03, "Specialty fluorochemicals"),

    # ============ REALTY / CONSTRUCTION ============
    # Real estate developers consume massive cement + steel volumes
    ("ULTRACEMCO.NS",  "DLF.NS",         0.02, "Cement for DLF projects"),
    ("AMBUJACEM.NS",   "GODREJPROP.NS",  0.02, "Cement supply for Godrej projects"),
    ("ACC.NS",         "OBEROIRLTY.NS",  0.02, "Cement for Mumbai residential projects"),
    ("TATASTEEL.NS",   "DLF.NS",         0.02, "Structural steel for high-rise"),
    ("JSWSTEEL.NS",    "GODREJPROP.NS",  0.02, "TMT and structural steel"),

    # ============ FMCG / CONSUMER EXPANSION ============
    # FMCG majors consume sugar, dairy proxies, palm oil (no listed Indian palm oil major)
    # Sugar mills already linked to Britannia/Nestle in existing edges; add Marico, Dabur
    ("BALRAMCHIN.NS",  "MARICO.NS",      0.02, "Sugar for confectionery edibles"),
    ("DHAMPURSUG.NS",  "ITC.NS",         0.03, "Sugar input for ITC foods division"),

    # ============ EMS / SEMICONDUCTOR PROXY CHAIN ============
    # Indian EMS (Kaynes, Dixon, Syrma) assemble for global chip clients but are downstream consumers
    # of international semis. They appear as customers of NVDA/AMD/etc — but those edges
    # cross into INTERNATIONAL tickers which aren't in the customer-supplier scope by design.
    # Cleaner Indian-only edges: Dixon supplies appliance brands that aren't in our universe
    # so the chain mostly lives outside our graph. Skipping for now — note added in OBSERVATIONS.
]


def get_suppliers_of(customer_ticker: str) -> list:
    return [
        {"Ticker": s, "Weight": w, "Note": n}
        for s, c, w, n in SUPPLY_CHAIN
        if c == customer_ticker
    ]


def get_customers_of(supplier_ticker: str) -> list:
    return [
        {"Ticker": c, "Weight": w, "Note": n}
        for s, c, w, n in SUPPLY_CHAIN
        if s == supplier_ticker
    ]


def all_tickers_in_graph() -> set:
    tickers = set()
    for s, c, _, _ in SUPPLY_CHAIN:
        tickers.add(s)
        tickers.add(c)
    return tickers