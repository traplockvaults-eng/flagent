// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * AIFlashLoanExecutor (Aave V3 flash loan receiver)
 * NOTE: Guardrails included, but audit before mainnet use.
 */

/* ============================= Interfaces ============================= */

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function balanceOf(address owner) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
    function decimals() external view returns (uint8);
}

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
}

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IFlashLoanSimpleReceiver {
    function ADDRESSES_PROVIDER() external view returns (IPoolAddressesProvider);
    function POOL() external view returns (IPool);
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

/* ============================= Libraries ============================= */

library SafeERC20 {
    function safeTransfer(IERC20 token, address to, uint256 value) internal {
        bytes memory data = abi.encodeWithSelector(token.transfer.selector, to, value);
        _call(token, data, "SafeERC20: transfer failed");
    }

    function safeTransferFrom(IERC20 token, address from, address to, uint256 value) internal {
        bytes memory data = abi.encodeWithSelector(token.transferFrom.selector, from, to, value);
        _call(token, data, "SafeERC20: transferFrom failed");
    }

    function safeApprove(IERC20 token, address spender, uint256 value) internal {
        bytes memory data = abi.encodeWithSelector(token.approve.selector, spender, 0);
        _call(token, data, "SafeERC20: approve reset failed");
        data = abi.encodeWithSelector(token.approve.selector, spender, value);
        _call(token, data, "SafeERC20: approve failed");
    }

    function _call(IERC20 token, bytes memory data, string memory err) private {
        (bool ok, bytes memory ret) = address(token).call(data);
        require(ok, err);
        if (ret.length > 0) {
            require(abi.decode(ret, (bool)), err);
        }
    }
}

/* ============================= Access/Guards ============================= */

abstract contract Ownable {
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Ownable: not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Ownable: zero addr");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}

abstract contract Pausable is Ownable {
    event Paused(address indexed by);
    event Unpaused(address indexed by);
    bool public paused;

    modifier whenNotPaused() {
        require(!paused, "Pausable: paused");
        _;
    }

    function pause() external onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }
}

abstract contract ReentrancyGuard {
    uint256 private _locked = 1;
    modifier nonReentrant() {
        require(_locked == 1, "ReentrancyGuard: reentrant");
        _locked = 2;
        _;
        _locked = 1;
    }
}

/* ============================= Executor ============================= */

contract AIFlashLoanExecutor is IFlashLoanSimpleReceiver, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    struct Call {
        address target;
        uint256 value;
        bytes data;
    }

    struct Approval {
        address token;
        address spender;
        uint256 amount;
    }

    struct FlashParams {
        uint256 minProfit;       // minimum profit in loan asset units (post-repayment)
        address beneficiary;     // where profit is sent; 0 keeps in contract
        Approval[] approvals;    // pre-execution approvals (exact amounts)
        Call[] calls;            // sequence of external calls (targets must be allowlisted)
    }

    IPoolAddressesProvider public immutable override ADDRESSES_PROVIDER;
    IPool public immutable override POOL;

    mapping(address => bool) public isAllowedTarget;
    mapping(address => bool) public isAllowedToken;
    bool public enforceTokenAllowlist;
    uint16 public referralCode;

    event AllowedTargetSet(address indexed target, bool allowed);
    event AllowedTokenSet(address indexed token, bool allowed);
    event EnforceTokenAllowlistSet(bool enabled);
    event ReferralCodeSet(uint16 referralCode);
    event ExternalCall(address indexed target, uint256 value, bytes data, bool success, bytes result);
    event FlashLoanPlanned(address indexed asset, uint256 amount, uint256 minProfit, address beneficiary);
    event FlashLoanExecuted(address indexed asset, uint256 amount, uint256 premium, uint256 profit);
    event Rescue(address indexed token, address indexed to, uint256 amount);
    event ProfitWithdrawn(address indexed token, address indexed to, uint256 amount);

    constructor(IPoolAddressesProvider provider_) {
        require(address(provider_) != address(0), "bad provider");
        ADDRESSES_PROVIDER = provider_;
        POOL = IPool(provider_.getPool());
        require(address(POOL) != address(0), "bad pool");
    }

    function setAllowedTarget(address target, bool allowed) external onlyOwner {
        isAllowedTarget[target] = allowed;
        emit AllowedTargetSet(target, allowed);
    }

    function batchSetAllowedTargets(address[] calldata targets, bool allowed) external onlyOwner {
        for (uint256 i = 0; i < targets.length; i++) {
            isAllowedTarget[targets[i]] = allowed;
            emit AllowedTargetSet(targets[i], allowed);
        }
    }

    function setAllowedToken(address token, bool allowed) external onlyOwner {
        isAllowedToken[token] = allowed;
        emit AllowedTokenSet(token, allowed);
    }

    function setEnforceTokenAllowlist(bool enabled) external onlyOwner {
        enforceTokenAllowlist = enabled;
        emit EnforceTokenAllowlistSet(enabled);
    }

    function setReferralCode(uint16 code) external onlyOwner {
        referralCode = code;
        emit ReferralCodeSet(code);
    }

    function executeFlashLoan(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner whenNotPaused nonReentrant {
        require(asset != address(0), "asset=0");
        if (enforceTokenAllowlist) {
            require(isAllowedToken[asset], "asset not allowed");
        }
        FlashParams memory p = _decodeParams(params);
        emit FlashLoanPlanned(asset, amount, p.minProfit, p.beneficiary);

        POOL.flashLoanSimple(address(this), asset, amount, params, referralCode);
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override whenNotPaused nonReentrant returns (bool) {
        require(msg.sender == address(POOL), "caller not pool");
        require(initiator == address(this), "bad initiator");
        if (enforceTokenAllowlist) {
            require(isAllowedToken[asset], "asset not allowed");
        }

        uint256 startingBal = IERC20(asset).balanceOf(address(this));
        require(startingBal >= amount, "insufficient borrowed");

        FlashParams memory p = _decodeParams(params);

        for (uint256 i = 0; i < p.approvals.length; i++) {
            Approval memory a = p.approvals[i];
            require(isAllowedTarget[a.spender], "spender not allowed");
            if (enforceTokenAllowlist) {
                require(isAllowedToken[a.token], "token not allowed");
            }
            IERC20(a.token).safeApprove(a.spender, a.amount);
        }

        for (uint256 i = 0; i < p.calls.length; i++) {
            Call memory c = p.calls[i];
            require(isAllowedTarget[c.target], "target not allowed");
            (bool ok, bytes memory ret) = c.target.call{value: c.value}(c.data);
            emit ExternalCall(c.target, c.value, c.data, ok, ret);
            require(ok, "external call failed");
        }

        uint256 owed = amount + premium;
        uint256 endingBal = IERC20(asset).balanceOf(address(this));
        require(endingBal >= owed, "insufficient to repay");

        uint256 profit = endingBal - owed;
        require(profit >= p.minProfit, "minProfit not met");

        IERC20(asset).safeApprove(address(POOL), owed);

        if (p.beneficiary != address(0) && profit > 0) {
            IERC20(asset).safeTransfer(p.beneficiary, profit);
            emit ProfitWithdrawn(asset, p.beneficiary, profit);
        }

        emit FlashLoanExecuted(asset, amount, premium, profit);
        return true;
    }

    function _decodeParams(bytes calldata params) internal pure returns (FlashParams memory p) {
        (p) = abi.decode(params, (FlashParams));
    }

    function rescue(address token, address to, uint256 amount) external onlyOwner {
        require(to != address(0), "to=0");
        IERC20(token).safeTransfer(to, amount);
        emit Rescue(token, to, amount);
    }

    receive() external payable {}
    fallback() external payable {}
}
