from mcp.server.fastmcp import FastMCP

# Use snake_case name to match manifest & orchestrator expectations
mcp = FastMCP(name="adder_server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two integers and returns the sum."""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="stdio")