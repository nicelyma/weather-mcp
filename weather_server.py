from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

def format_alert(f: dict) -> str:
    p = f["properties"]
    return (
        f"Event: {p.get('event', 'Unknown')}\n"
        f"Area: {p.get('areaDesc', 'Unknown')}\n"
        f"Severity: {p.get('severity', 'Unknown')}\n"
        f"Description: {p.get('description', 'No description available')}\n"
        f"Instructions: {p.get('instruction', 'No specific instructions provided')}\n"
    )

@mcp.tool()
async def get_alerts(state: str) -> str:
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or not data.get("features"):
        return "No active alerts or unable to fetch alerts."
    return "\n---\n".join(format_alert(x) for x in data["features"])

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    pts = await make_nws_request(f"{NWS_API_BASE}/points/{latitude},{longitude}")
    if not pts:
        return "Unable to fetch forecast data for this location."
    fc = await make_nws_request(pts["properties"]["forecast"])
    if not fc:
        return "Unable to fetch detailed forecast."
    periods = fc["properties"]["periods"][:5]
    return "\n---\n".join(
        (
            f"{p['name']}:\n"
            f"Temperature: {p['temperature']}°{p['temperatureUnit']}\n"
            f"Wind: {p['windSpeed']} {p['windDirection']}\n"
            f"Forecast: {p['detailedForecast']}\n"
        )
        for p in periods
    )

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
