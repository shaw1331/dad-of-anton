from __future__ import annotations


def format_stock_summary(stock_data: dict) -> str:
    """Format stock data into a readable summary."""
    sections = [
        format_stock_header(stock_data),
        format_financial_ratios(stock_data),
        format_quarterly_results(stock_data),
        format_shareholding(stock_data),
        format_pros_cons(stock_data),
    ]
    return "\n\n".join(s for s in sections if s)


def format_stock_header(stock_data: dict) -> str:
    """Format the stock header with basic info."""
    ticker = stock_data.get("ticker", "N/A")
    name = stock_data.get("company_name") or stock_data.get("name", "N/A")
    sector = stock_data.get("sector") or "N/A"
    industry = stock_data.get("industry") or "N/A"

    return (
        f"Stock: {ticker} — {name}\n"
        f"Sector: {sector}\n"
        f"Industry: {industry}"
    )


def format_financial_ratios(stock_data: dict) -> str:
    """Format the financial ratios section."""
    data = stock_data.get("data", {})
    ratios = data.get("ratios", {})
    if not ratios:
        return ""

    lines = ["Financial Ratios:"]
    for key, value in ratios.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_quarterly_results(stock_data: dict) -> str:
    """Format the quarterly results section."""
    data = stock_data.get("data", {})
    quarterly = data.get("quarterly", {})
    if not quarterly:
        return ""

    lines = ["Latest Quarter Results:"]
    for key, value in quarterly.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_shareholding(stock_data: dict) -> str:
    """Format the shareholding pattern section."""
    data = stock_data.get("data", {})
    shareholding = data.get("shareholding", {})
    if not shareholding:
        return ""

    lines = ["Shareholding Pattern:"]
    for key, value in shareholding.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_pros_cons(stock_data: dict) -> str:
    """Format the pros and cons section."""
    data = stock_data.get("data", {})
    pros = data.get("pros", [])
    cons = data.get("cons", [])

    if not pros and not cons:
        return ""

    sections = []
    if pros:
        sections.append("Pros:")
        for item in pros:
            sections.append(f"  + {item}")
    if cons:
        sections.append("Cons:")
        for item in cons:
            sections.append(f"  - {item}")
    return "\n".join(sections)
