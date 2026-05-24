"""
The universe of stocks and commodities we analyze.
Now covers 13 sectors, ~75 Indian stocks, 8 commodities, and 18 international tickers.
Each addition has a specific analytical reason — see comments per group.
"""

# Commodities — liquid US-listed ETFs as proxies.
COMMODITIES = {
    "Gold":         "GLD",
    "Silver":       "SLV",
    "Crude Oil":    "USO",
    "Brent Crude":  "BNO",       # different from WTI, often diverges
    "Copper":       "CPER",
    "Natural Gas":  "UNG",
    "Aluminum":     "JJU",
    "Zinc":         "ZINC=F",    # try this; if it fails we'll swap
    "Sugar":        "CANE",
    "Steel":        "SLX",
    "Wheat":        "WEAT",
    "Corn":         "CORN",
    "Cotton":       "BAL",
    "Coffee":       "JO",
}

# Indian stocks grouped by sector.
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
        "JINDALSTEL.NS": "Jindal Steel",
        "HINDZINC.NS":   "Hindustan Zinc",
        "MOIL.NS":       "MOIL",
    },
    "Oil & Gas": {
        "RELIANCE.NS":  "Reliance",
        "ONGC.NS":      "ONGC",
        "IOC.NS":       "Indian Oil",
        "BPCL.NS":      "BPCL",
        "HINDPETRO.NS": "HPCL",
        "GAIL.NS":      "GAIL",
        "PETRONET.NS":  "Petronet LNG",
        "OIL.NS":       "Oil India",
        "MGL.NS":       "Mahanagar Gas",
        "IGL.NS":       "Indraprastha Gas",
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
        "EICHERMOT.NS":  "Eicher Motors",
        "TVSMOTOR.NS":   "TVS Motor",
        "ASHOKLEY.NS":   "Ashok Leyland",
        "BOSCHLTD.NS":   "Bosch",
        "MOTHERSON.NS":  "Motherson Sumi",
        "SUBROS.NS":     "Subros",
        "SONACOMS.NS":   "Sona BLW",
        "EXIDEIND.NS":   "Exide Industries",
        "MRF.NS":        "MRF",
        "APOLLOTYRE.NS": "Apollo Tyres",
        "CEATLTD.NS":    "CEAT",
    },
    "Capital Goods & Infra": {
        "LT.NS":         "Larsen & Toubro",
        "SIEMENS.NS":    "Siemens India",
        "ABB.NS":        "ABB India",
        "BHEL.NS":       "BHEL",
        "CUMMINSIND.NS": "Cummins India",
        "THERMAX.NS":    "Thermax",
        "KEC.NS":        "KEC International",
        "KPIL.NS":       "Kalpataru Projects",
        "GRINDWELL.NS":  "Grindwell Norton",
        "AIAENG.NS":     "AIA Engineering",
        "TIMKEN.NS":     "Timken India",
        "SKFINDIA.NS":   "SKF India",
    },
    "Cement": {
        "ULTRACEMCO.NS": "UltraTech Cement",
        "SHREECEM.NS":   "Shree Cement",
        "AMBUJACEM.NS":  "Ambuja Cement",
        "ACC.NS":        "ACC",
        "DALBHARAT.NS":  "Dalmia Bharat",
        "JKCEMENT.NS":   "JK Cement",
        "RAMCOCEM.NS":   "Ramco Cements",
    },
    "Specialty Chemicals & Fertilizers": {
        "SRF.NS":         "SRF",
        "AARTIIND.NS":    "Aarti Industries",
        "DEEPAKNTR.NS":   "Deepak Nitrite",
        "UPL.NS":         "UPL",
        "COROMANDEL.NS":  "Coromandel International",
        "CHAMBLFERT.NS":  "Chambal Fertilizers",
        "PIIND.NS":       "PI Industries",
        "GNFC.NS":        "GNFC",
        "NAVINFLUOR.NS":  "Navin Fluorine",
        "VINATIORGA.NS":  "Vinati Organics",
        "ATUL.NS":        "Atul",
        "TATACHEM.NS":    "Tata Chemicals",
    },
    "Consumer / FMCG": {
        "NESTLEIND.NS":  "Nestle India",
        "BRITANNIA.NS":  "Britannia",
        "MARICO.NS":     "Marico",
        "DABUR.NS":      "Dabur",
        "TATACONSUM.NS": "Tata Consumer",
        "HINDUNILVR.NS": "HUL",
        "ITC.NS":        "ITC",
        "GODREJCP.NS":   "Godrej Consumer",
        "COLPAL.NS":     "Colgate-Palmolive",
        "EMAMILTD.NS":   "Emami",
    },
    "IT & Tech": {
        "TCS.NS":      "TCS",
        "INFY.NS":     "Infosys",
        "WIPRO.NS":    "Wipro",
        "HCLTECH.NS":  "HCL Tech",
        "TECHM.NS":    "Tech Mahindra",
        "PERSISTENT.NS": "Persistent Systems",
        "COFORGE.NS":  "Coforge",
        "MPHASIS.NS":  "Mphasis",
    },
    "EMS & AI-adjacent Tech": {
        "KAYNES.NS":    "Kaynes Technology",
        "DIXON.NS":     "Dixon Technologies",
        "SYRMA.NS":     "Syrma SGS",
        "AMBER.NS":     "Amber Enterprises",
        "CYIENT.NS":    "Cyient",
        "TATAELXSI.NS": "Tata Elxsi",
        "LTTS.NS":      "L&T Technology Services",
    },
    "Defense & Aerospace": {
        "HAL.NS":          "Hindustan Aeronautics",
        "BEL.NS":          "Bharat Electronics",
        "BDL.NS":          "Bharat Dynamics",
        "MAZDOCK.NS":      "Mazagon Dock",
        "COCHINSHIP.NS":   "Cochin Shipyard",
        "DATAPATTNS.NS":   "Data Patterns",
        "PARAS.NS":        "Paras Defence",
        "ASTRAMICRO.NS":   "Astra Microwave",
    },
    "Power & Utilities": {
        "NTPC.NS":     "NTPC",
        "POWERGRID.NS": "Power Grid Corp",
        "TATAPOWER.NS": "Tata Power",
        "JSWENERGY.NS": "JSW Energy",
        "ADANIGREEN.NS": "Adani Green Energy",
        "ADANIPOWER.NS": "Adani Power",
        "NHPC.NS":     "NHPC",
        "SJVN.NS":     "SJVN",
        "TORNTPOWER.NS": "Torrent Power",
        "CESC.NS":     "CESC",
    },
    "Pharma & Healthcare": {
        "SUNPHARMA.NS":  "Sun Pharma",
        "DRREDDY.NS":    "Dr Reddy's",
        "CIPLA.NS":      "Cipla",
        "DIVISLAB.NS":   "Divi's Labs",
        "LUPIN.NS":      "Lupin",
        "AUROPHARMA.NS": "Aurobindo Pharma",
        "GLENMARK.NS":   "Glenmark Pharma",
        "TORNTPHARM.NS": "Torrent Pharma",
        "ZYDUSLIFE.NS":  "Zydus Lifesciences",
        "ALKEM.NS":      "Alkem Labs",
        "BIOCON.NS":     "Biocon",
        "APOLLOHOSP.NS": "Apollo Hospitals",
        "MAXHEALTH.NS":  "Max Healthcare",
        "FORTIS.NS":     "Fortis Healthcare",
    },
    "Banking & Financials": {
        "HDFCBANK.NS":  "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "SBIN.NS":      "State Bank of India",
        "AXISBANK.NS":  "Axis Bank",
        "KOTAKBANK.NS": "Kotak Mahindra Bank",
        "INDUSINDBK.NS": "IndusInd Bank",
        "BAJFINANCE.NS": "Bajaj Finance",
        "BAJAJFINSV.NS": "Bajaj Finserv",
        "SBILIFE.NS":    "SBI Life",
        "HDFCLIFE.NS":   "HDFC Life",
        "ICICIPRULI.NS": "ICICI Prudential Life",
        "ICICIGI.NS":    "ICICI Lombard",
    },
    "Realty & Construction": {
        "DLF.NS":         "DLF",
        "GODREJPROP.NS":  "Godrej Properties",
        "OBEROIRLTY.NS":  "Oberoi Realty",
        "PRESTIGE.NS":    "Prestige Estates",
        "PHOENIXLTD.NS":  "Phoenix Mills",
        "SOBHA.NS":       "Sobha",
    },
    "Aviation & Hospitality": {
        "INDIGO.NS":       "InterGlobe Aviation",
        "INDHOTEL.NS":     "Indian Hotels",
        "LEMONTREE.NS":    "Lemon Tree Hotels",
    },
    "Telecom": {
        "BHARTIARTL.NS": "Bharti Airtel",
        "INDUSTOWER.NS": "Indus Towers",
        "HFCL.NS":       "HFCL",
        "TEJASNET.NS":   "Tejas Networks",
    },
    "Textiles & Agri-export": {
        "PAGEIND.NS":   "Page Industries",
        "TRENT.NS":     "Trent",
        "AVANTIFEED.NS": "Avanti Feeds",
        "APEXFROZN.NS": "Apex Frozen Foods",
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