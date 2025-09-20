/*
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import “forge-std/Script.sol”;
import “…/src/AIFlashLoanExecutor.sol”;
contract Deploy is Script {
function run() external {
address provider = vm.envAddress(“AAVE_V3_ADDRESSES_PROVIDER”);
uint256 pk = vm.envUint(“PRIVATE_KEY”);
Plain Text
Copy
    vm.startBroadcast(pk);
    AIFlashLoanExecutor exec = new AIFlashLoanExecutor(IPoolAddressesProvider(provider));
    console2.log("AIFlashLoanExecutor:", address(exec));
    vm.stopBroadcast();
}
}
*/