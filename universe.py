"""
The universe of stocks and commodities we analyze.
Add new tickers here; everything else picks them up automatically.
"""

# Commodities — using liquid US-listed ETFs as proxies.
# These trade in USD but for CORRELATION (which uses returns, not prices)
# the currency doesn't matter.
COMMODITIES = {
    "Gold":      "GLD",
    "Silver":    "SLV",
    "Crude Oil": "USO",
    "Copper":    "CPER",
    "Natural Gas": "UNG",
    "Aluminum":  "JJU",   # less liquid but works
    "Sugar":     "CANE",
    "Steel":     "SLX",
}

# Indian stocks grouped by sector.
# .NS suffix = NSE India listing.
# Picked names with clear commodity exposure for interesting results.
STOCKS = {
    "Jewellery": {
        "TITAN.NS":   "Titan",
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
        "POLYCAB.NS":  "Polycab",
        "KEI.NS":      "KEI Industries",
        "HAVELLS.NS":  "Havells",
        "FINCABLES.NS": "Finolex Cables",
    },
    "Metals & Mining": {
        "TATASTEEL.NS": "Tata Steel",
        "JSWSTEEL.NS":  "JSW Steel",
        "HINDALCO.NS":  "Hindalco",
        "VEDL.NS":      "Vedanta",
        "NMDC.NS":      "NMDC",
        "SAIL.NS":      "SAIL",
        "NATIONALUM.NS": "NALCO",
    },
    "Oil & Gas": {
        "RELIANCE.NS": "Reliance",
        "ONGC.NS":     "ONGC",
        "IOC.NS":      "Indian Oil",
        "BPCL.NS":     "BPCL",
        "HINDPETRO.NS": "HPCL",
        "GAIL.NS":     "GAIL",
        "PETRONET.NS": "Petronet LNG",
    },
    "Sugar": {
        "BALRAMCHIN.NS": "Balrampur Chini",
        "DHAMPURSUG.NS": "Dhampur Sugar",
        "TRIVENI.NS":    "Triveni Engg",
        "BAJAJHIND.NS":  "Bajaj Hindusthan",
    },
    "Auto (steel + aluminum-linked)": {
        "MARUTI.NS":  "Maruti Suzuki",
        "TATAMOTORS.NS": "Tata Motors",
        "M&M.NS":     "Mahindra",
        "BAJAJ-AUTO.NS": "Bajaj Auto",
        "HEROMOTOCO.NS": "Hero MotoCorp",
        "BHARATFORG.NS": "Bharat Forge",
    },
}

# Flatten into a single dict for easy lookups: ticker -> display name
ALL_STOCKS = {ticker: name for sector in STOCKS.values() for ticker, name in sector.items()}

# Reverse: ticker -> its sector
STOCK_SECTOR = {
    ticker: sector_name
    for sector_name, stocks in STOCKS.items()
    for ticker in stocks
}
# International tickers — used for "leader scan" and pattern matching against global moves
INTERNATIONAL = {
    # US tech / semis (often lead Indian IT and EMS)
    "NVDA": "Nvidia",
    "AMD": "AMD",
    "AVGO": "Broadcom",
    "TSM": "TSMC",
    "INTC": "Intel",
    # US industrials & materials
    "CAT": "Caterpillar",
    "DE": "Deere",
    "FCX": "Freeport-McMoRan",  # copper
    "NUE": "Nucor",              # steel
    # US autos
    "TSLA": "Tesla",
    "F": "Ford",
    "GM": "GM",
    # US consumer
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola",
    # US energy
    "XOM": "ExxonMobil",
    "CVX": "Chevron",
    # India ADRs (useful as direct cross-checks)
    "INFY": "Infosys ADR",
    "WIT":  "Wipro ADR",
    "HDB":  "HDFC Bank ADR",
}