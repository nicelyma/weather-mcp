"""
Weather MCP Server
==================
提供两个工具：
1. get_alerts(state)        —— 返回指定美国州当前气象预警
2. get_forecast(lat, lon)   —— 返回指定坐标点未来 5 个时段预报
"""

from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# 全局 HTTP 客户端（复用连接池）
CLIENT = httpx.AsyncClient(
    headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"},
    timeout=30.0,
)

async def make_nws_request(url: str) -> Optional[dict[str, Any]]:
    try:
        resp = await CLIENT.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def format_alert(feature: dict) -> str:
    p = feature["properties"]
    return (
        f"Event: {p.get('event', 'Unknown')}\n"
        f"Area: {p.get('areaDesc', 'Unknown')}\n"
        f"Severity: {p.get('severity', 'Unknown')}\n"
        f"Description: {p.get('description', 'No description available')}\n"
        f"Instructions: {p.get('instruction', 'No specific instructions provided')}\n"
    )

# ----------------------------------------------------------------------
# MCP 工具
# ----------------------------------------------------------------------
@mcp.tool()
async def get_alerts(state: str) -> str:
    """根据两位州码返回当前气象预警（无则提示）"""
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = await make_nws_request(url)
    if not data or not data.get("features"):
        return "No active alerts or unable to fetch alerts."
    return "\n---\n".join(format_alert(x) for x in data["features"])


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """返回指定坐标未来 5 段天气预报"""
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

# ----------------------------------------------------------------------
# 入口：HTTP 方式，端口 8080
# ----------------------------------------------------------------------
def main() -> None:
    mcp.run(transport="http", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        raise
