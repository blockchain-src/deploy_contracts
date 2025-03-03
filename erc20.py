from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version
import sys

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# 连接 Web3
RPC_URL = "https://withered-patient-glade.monad-testnet.quiknode.pro/0155507fe08fe4d1e2457a85f65b4bc7e6ed522f"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

print()
print(f"{YELLOW}{BOLD}🔗 正在连接到 RPC...{RESET}")
if not w3.is_connected():
    print(f"{RED}{BOLD}❌ 连接失败！请检查 RPC_URL 配置{RESET}\n")
    sys.exit(1)
print(f"{GREEN}{BOLD}✅ 连接成功！{RESET}\n")

# 输入私钥列表
print(f"{YELLOW}{BOLD}🔑 请输入您的私钥列表，每行一个，按两次回车确认:{RESET}")
private_keys = []
while True:
    line = input().strip()
    if line == "":
        break
    if not line.startswith("0x") or len(line) != 66:
        print(f"{RED}{BOLD}❌ 无效的私钥格式: {line}{RESET}\n")
        continue
    private_keys.append(line)

if not private_keys:
    print(f"{RED}{BOLD}❌ 没有输入有效的私钥！{RESET}\n")
    sys.exit(1)

# Solidity 合约
erc20_contract = """
pragma solidity ^0.8.0;
contract MyToken {
    string public name = "HODL";
    string public symbol = "HODL";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 value);
    constructor(uint256 initialSupply) {
        totalSupply = initialSupply * 10 ** uint256(decimals);
        balanceOf[msg.sender] = totalSupply;
    }
    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "ERC20: transfer to zero address");
        require(balanceOf[msg.sender] >= amount, "ERC20: insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
}
"""

print(f"{YELLOW}{BOLD}📦 正在编译 Solidity 合约...{RESET}\n")
install_solc("0.8.0")
set_solc_version("0.8.0")
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"MyToken.sol": {"content": erc20_contract}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
})
abi = compiled_sol['contracts']['MyToken.sol']['MyToken']['abi']
bytecode = compiled_sol['contracts']['MyToken.sol']['MyToken']['evm']['bytecode']['object']

print(f"{GREEN}{BOLD}✅ 合约编译完成！{RESET}\n")

# 依次部署合约
for private_key in private_keys:
    account = w3.eth.account.from_key(private_key)
    my_address = w3.to_checksum_address(account.address)
    balance = w3.eth.get_balance(my_address)
    gas_price = w3.eth.gas_price
    estimated_gas = 2_000_000
    
    print(f"{CYAN}{BOLD}📌 钱包地址: {my_address}{RESET}")
    print(f"💰 余额: {w3.from_wei(balance, 'ether'):.5f} MON\n")
    
    if balance < estimated_gas * gas_price:
        print(f"{RED}{BOLD}⚠️ 余额不足，跳过部署{RESET}\n")
        continue
    
    try:
        MyToken = w3.eth.contract(abi=abi, bytecode=bytecode)
        transaction = MyToken.constructor(1_000_000_000).build_transaction({
            'gas': estimated_gas,
            'gasPrice': gas_price,
            'from': my_address,
            'nonce': w3.eth.get_transaction_count(my_address),
        })
        signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.raw_transaction)
        
        print(f"{YELLOW}{BOLD}🚀 正在部署合约...{RESET}")
        print(f"⏳ 交易哈希: {tx_hash.hex()}\n")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"{GREEN}{BOLD}✅ 代币合约部署成功！合约地址: {receipt['contractAddress']}{RESET}\n")
    except Exception as e:
        print(f"{RED}{BOLD}❌ 部署失败: {e}{RESET}\n")
