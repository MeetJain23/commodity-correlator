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