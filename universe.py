"""
The universe of stocks and commodities we analyze.
Now covers 13 sectors, ~75 Indian stocks, 8 commodities, and 18 international tickers.
Each addition has a specific analytical reason — see comments per group.
"""

# Commodities — liquid US-listed ETFs as proxies.
COMMODITIES = {
    "Gold":      "GLD",
    "Silver":    "SLV",
    "Crude Oil": "USO",
    "Copper":    "CPER",
    "Natural Gas": "UNG",
    "Aluminum":  "JJU",
    "Sugar":     "CANE",
    "Steel":     "SLX",
}

# Indian stocks grouped by sector.
STOCKS = {
    "Jewellery": {
        "TITAN.NS":      "Titan",
        "KALYANKJIL.NS": "Kalyan Jewellers",
        "PCJEWELLER.NS": "PC Jeweller",
    },
    "Paints & Chemicals (crude-linked)": {
        "ASIANPAINT.NS": "Asian Paints",
        "BERGEPAINT.NS": "Berger Paints",
        "PIDILITIND.NS": "Pidilite",
        "AKZOINDIA.NS":  "Akzo Nobel India",
    },
    "Cables & Wires (copper-linked)": {
        "POLYCAB.NS":   "Polycab",
        "KEI.NS":       "KEI Industries",
        "HAVELLS.NS":   "Havells",
        "FINCABLES.NS": "Finolex Cables",
    },
    "Metals & Mining": {
        "TATASTEEL.NS":  "Tata Steel",
        "JSWSTEEL.NS":   "JSW Steel",
        "HINDALCO.NS":   "Hindalco",
        "VEDL.NS":       "Vedanta",
        "NMDC.NS":       "NMDC",
        "SAIL.NS":       "SAIL",
        "NATIONALUM.NS": "NALCO",
    },
    "Oil & Gas": {
        "RELIANCE.NS":  "Reliance",
        "ONGC.NS":      "ONGC",
        "IOC.NS":       "Indian Oil",
        "BPCL.NS":      "BPCL",
        "HINDPETRO.NS": "HPCL",
        "GAIL.NS":      "GAIL",
        "PETRONET.NS":  "Petronet LNG",
    },
    "Sugar": {
        "BALRAMCHIN.NS": "Balrampur Chini",
        "DHAMPURSUG.NS": "Dhampur Sugar",
        "TRIVENI.NS":    "Triveni Engg",
        "BAJAJHIND.NS":  "Bajaj Hindusthan",
    },
    "Auto (steel + aluminum-linked)": {
        "MARUTI.NS":     "Maruti Suzuki",
        "M&M.NS":        "Mahindra",
        "BAJAJ-AUTO.NS": "Bajaj Auto",
        "HEROMOTOCO.NS": "Hero MotoCorp",
        "BHARATFORG.NS": "Bharat Forge",
    },
    # --- NEW GROUPS BELOW ---

    # Capital Goods & Infra — completes the steel/aluminum/copper DOWNSTREAM picture.
    # These are real buyers of metals; supply chain cascades from metals now flow somewhere.
    "Capital Goods & Infra": {
        "LT.NS":        "Larsen & Toubro",
        "SIEMENS.NS":   "Siemens India",
        "ABB.NS":       "ABB India",
        "BHEL.NS":      "BHEL",
        "CUMMINSIND.NS": "Cummins India",
        "THERMAX.NS":   "Thermax",
        "KEC.NS":       "KEC International",
        "KPIL.NS":      "Kalpataru Projects",
    },

    # Cement — own cyclical commodity-like behavior + strong monsoon seasonality.
    "Cement": {
        "ULTRACEMCO.NS": "UltraTech Cement",
        "SHREECEM.NS":   "Shree Cement",
        "AMBUJACEM.NS":  "Ambuja Cement",
        "ACC.NS":        "ACC",
        "DALBHARAT.NS":  "Dalmia Bharat",
    },

    # Specialty Chemicals & Fertilizers — crude/gas exposure on input side, complex downstream.
    # Huge gap in earlier universe.
    "Specialty Chemicals & Fertilizers": {
        "SRF.NS":         "SRF",
        "AARTIIND.NS":    "Aarti Industries",
        "DEEPAKNTR.NS":   "Deepak Nitrite",
        "UPL.NS":         "UPL",
        "COROMANDEL.NS":  "Coromandel International",
        "CHAMBLFERT.NS":  "Chambal Fertilizers",
    },

    # Consumer / FMCG — strong festive seasonality, sugar/agri downstream.
    "Consumer / FMCG": {
        "NESTLEIND.NS":  "Nestle India",
        "BRITANNIA.NS":  "Britannia",
        "MARICO.NS":     "Marico",
        "DABUR.NS":      "Dabur",
        "TATACONSUM.NS": "Tata Consumer",
    },

    # IT & Tech — Indian side of global tech move (for international leader scans).
    "IT & Tech": {
        "TCS.NS":         "TCS",
        "INFY.NS":        "Infosys",
        "WIPRO.NS":       "Wipro",
        "HCLTECH.NS":     "HCL Tech",
        "TECHM.NS":       "Tech Mahindra",
    },

    # Telecom — already had some, formalized as a sector for clarity.
    "Telecom": {
        "BHARTIARTL.NS": "Bharti Airtel",
        "INDUSTOWER.NS": "Indus Towers",
        "HFCL.NS":       "HFCL",
    },
}

# Flatten
ALL_STOCKS = {ticker: name for sector in STOCKS.values() for ticker, name in sector.items()}

STOCK_SECTOR = {
    ticker: sector_name
    for sector_name, stocks in STOCKS.items()
    for ticker in stocks
}

# International tickers — for International Leader Scan + cross-market analysis.
INTERNATIONAL = {
    # US tech / semis
    "NVDA": "Nvidia",
    "AMD":  "AMD",
    "AVGO": "Broadcom",
    "TSM":  "TSMC",
    "INTC": "Intel",
    # US industrials & materials
    "CAT": "Caterpillar",
    "DE":  "Deere",
    "FCX": "Freeport-McMoRan",
    "NUE": "Nucor",
    # US autos
    "TSLA": "Tesla",
    "F":    "Ford",
    "GM":   "GM",
    # US consumer
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola",
    # US energy
    "XOM": "ExxonMobil",
    "CVX": "Chevron",
    # India ADRs
    "INFY": "Infosys (already in NS list — ADR cross-check)",  # already covered via .NS
    "WIT":  "Wipro ADR",
    "HDB":  "HDFC Bank ADR",
}