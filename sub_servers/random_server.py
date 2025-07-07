import random
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="random_server")


@mcp.tool()
def generate_random(minimum: int = 0, maximum: int = 100) -> int:
    """Generates a random integer within a specified range."""
    return random.randint(minimum, maximum)


if __name__ == "__main__":
    mcp.run(transport="stdio") 