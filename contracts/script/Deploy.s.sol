/*
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/AIFlashLoanExecutor.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(pk);
        AIFlashLoanExecutor exec = new AIFlashLoanExecutor();
        console2.log("AIFlashLoanExecutor:", address(exec));
        vm.stopBroadcast();
    }
}
*/
