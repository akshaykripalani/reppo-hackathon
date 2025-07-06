from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="AdderServer")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two integers and returns the sum."""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="stdio")