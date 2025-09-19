// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../../contracts/src/AIFlashLoanExecutor.sol";

interface IUniswapV2Router {
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory);
}

interface IERC20like {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
}

address constant AAVE_V3_PROVIDER_MAINNET = 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb;
address constant UNIV2_ROUTER_MAINNET   = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
address constant SUSHI_ROUTER_MAINNET   = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
address constant WETH_MAINNET           = 0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2;
address constant USDC_MAINNET           = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

contract AIFlashLoanExecutorV2ArbForkTest is Test {
    AIFlashLoanExecutor exec;

    function setUp() public {
        string memory rpc = vm.envString("MAINNET_RPC_URL");
        // Optionally pin a block for determinism
        // uint256 fork = vm.createFork(rpc, 19_000_000);
        uint256 fork = vm.createFork(rpc);
        vm.selectFork(fork);

        exec = new AIFlashLoanExecutor(IPoolAddressesProvider(AAVE_V3_PROVIDER_MAINNET));

        // Allow routers and tokens
        exec.setAllowedTarget(UNIV2_ROUTER_MAINNET, true);
        exec.setAllowedTarget(SUSHI_ROUTER_MAINNET, true);
        exec.setAllowedToken(WETH_MAINNET, true);
        exec.setAllowedToken(USDC_MAINNET, true);
        exec.setEnforceTokenAllowlist(true);
    }

    function test_V2CycleFlashLoan_AttemptCycleIfProfitable() public {
        uint256 amountIn = 5 ether;

        // Prefund small buffer to cover premium in worst case
        deal(WETH_MAINNET, address(exec), 0.01 ether);

        // Check quotes: WETH->USDC on Uni, USDC->WETH on Sushi and alternate
        address[] memory path1 = new address[](2);
        path1[0] = WETH_MAINNET; path1[1] = USDC_MAINNET;

        address[] memory path2 = new address[](2);
        path2[0] = USDC_MAINNET; path2[1] = WETH_MAINNET;

        uint[] memory uniOut = IUniswapV2Router(UNIV2_ROUTER_MAINNET).getAmountsOut(amountIn, path1);
        uint outMidUni = uniOut[1];
        uint[] memory sushiBack = IUniswapV2Router(SUSHI_ROUTER_MAINNET).getAmountsOut(outMidUni, path2);
        uint outBackUniSushi = sushiBack[1];

        uint[] memory sushiOut = IUniswapV2Router(SUSHI_ROUTER_MAINNET).getAmountsOut(amountIn, path1);
        uint outMidSushi = sushiOut[1];
        uint[] memory uniBack = IUniswapV2Router(UNIV2_ROUTER_MAINNET).getAmountsOut(outMidSushi, path2);
        uint outBackSushiUni = uniBack[1];

        // Choose the better cycle
        bool uniThenSushi = outBackUniSushi > outBackSushiUni;
        uint bestOutBack = uniThenSushi ? outBackUniSushi : outBackSushiUni;
        uint premium = (amountIn * 5) / 10_000;

        if (bestOutBack <= amountIn + premium) {
            emit log_string("No profitable cycle found at this block; skipping execution");
            return; // Skip test run; environment-dependent
        }

        // Build FlashParams with minOut backstops and approvals
        AIFlashLoanExecutor.Approval[] memory approvals = new AIFlashLoanExecutor.Approval[](2);
        AIFlashLoanExecutor.Call[] memory calls = new AIFlashLoanExecutor.Call[](2);

        address routerA = uniThenSushi ? UNIV2_ROUTER_MAINNET : SUSHI_ROUTER_MAINNET;
        address routerB = uniThenSushi ? SUSHI_ROUTER_MAINNET : UNIV2_ROUTER_MAINNET;

        // Approval 1: WETH -> routerA
        approvals[0] = AIFlashLoanExecutor.Approval({
            token: WETH_MAINNET,
            spender: routerA,
            amount: amountIn
        });
        // Approval 2: USDC -> routerB (approve estimated middle output)
        approvals[1] = AIFlashLoanExecutor.Approval({
            token: USDC_MAINNET,
            spender: routerB,
            amount: uniThenSushi ? outMidUni : outMidSushi
        });

        // Encode swaps with on-chain minOut backstops
        uint slip = 50; // 0.5%
        uint minOutMid = (uniThenSushi ? outMidUni : outMidSushi) * (10_000 - slip) / 10_000;
        uint minOutBack = bestOutBack * (10_000 - slip) / 10_000;

        bytes memory sel = bytes4(keccak256("swapExactTokensForTokens(uint256,uint256,address[],address,uint256)"));
        bytes memory data1 = abi.encodeWithSelector(
            sel,
            amountIn,
            minOutMid,
            path1,
            address(exec),
            block.timestamp + 600
        );
        bytes memory data2 = abi.encodeWithSelector(
            sel,
            uniThenSushi ? outMidUni : outMidSushi,
            minOutBack,
            path2,
            address(exec),
            block.timestamp + 600
        );

        calls[0] = AIFlashLoanExecutor.Call({target: routerA, value: 0, data: data1});
        calls[1] = AIFlashLoanExecutor.Call({target: routerB, value: 0, data: data2});

        AIFlashLoanExecutor.FlashParams memory p = AIFlashLoanExecutor.FlashParams({
            minProfit: 0, // rely on minOut and manual profit check here
            beneficiary: address(0),
            approvals: approvals,
            calls: calls
        });

        uint pre = IERC20like(WETH_MAINNET).balanceOf(address(exec));
        exec.executeFlashLoan(WETH_MAINNET, amountIn, abi.encode(p));
        uint post = IERC20like(WETH_MAINNET).balanceOf(address(exec));

        emit log_named_uint("WETH delta", post - pre);
        assertTrue(post >= pre + 1, "expected positive delta after premium");
    }
}
