# Minimal ABI fragments for Uniswap V2/V3 routers and quoter

UNISWAP_V2_ROUTER_ABI = [
    {
        "type":"function","name":"getAmountsOut","stateMutability":"view",
        "inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],
        "outputs":[{"name":"amounts","type":"uint256[]"}]
    },
    {
        "type":"function","name":"swapExactTokensForTokens","stateMutability":"nonpayable",
        "inputs":[
            {"name":"amountIn","type":"uint256"},
            {"name":"amountOutMin","type":"uint256"},
            {"name":"path","type":"address[]"},
            {"name":"to","type":"address"},
            {"name":"deadline","type":"uint256"}
        ],
        "outputs":[{"name":"amounts","type":"uint256[]"}]
    }
]

# Uniswap V3 QuoterV2 exactInputSingle and SwapRouter exactInputSingle
UNISWAP_V3_QUOTER_ABI = [
    {
        "type":"function","name":"quoteExactInputSingle","stateMutability":"view",
        "inputs":[
            {"name":"tokenIn","type":"address"},
            {"name":"tokenOut","type":"address"},
            {"name":"fee","type":"uint24"},
            {"name":"amountIn","type":"uint256"},
            {"name":"sqrtPriceLimitX96","type":"uint160"}
        ],
        "outputs":[{"name":"amountOut","type":"uint256"}]
    }
]

UNISWAP_V3_SWAP_ROUTER_ABI = [
    {
        "type":"function","name":"exactInputSingle","stateMutability":"payable",
        "inputs":[
            {"name":"params","type":"tuple","components":[
                {"name":"tokenIn","type":"address"},
                {"name":"tokenOut","type":"address"},
                {"name":"fee","type":"uint24"},
                {"name":"recipient","type":"address"},
                {"name":"deadline","type":"uint256"},
                {"name":"amountIn","type":"uint256"},
                {"name":"amountOutMinimum","type":"uint256"},
                {"name":"sqrtPriceLimitX96","type":"uint160"}
            ]}
        ],
        "outputs":[{"name":"amountOut","type":"uint256"}]
    }
]
