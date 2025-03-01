from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version
import json
import sys
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

# 2. 连接 Web3
RPC_URL = "https://withered-patient-glade.monad-testnet.quiknode.pro/0155507fe08fe4d1e2457a85f65b4bc7e6ed522f"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print(f"{RED}{BOLD}❌ 连接失败！请检查 RPC_URL 配置{RESET}")
    sys.exit(1)

# 3. 获取钱包地址
account = w3.eth.account.from_key(private_key)
my_address = w3.to_checksum_address(account.address)
print(f"{CYAN}{BOLD}📌 钱包地址: {my_address}{RESET}")

# 4. 编译 Solidity ERC-721 合约
erc721_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "./contracts/token/ERC721/ERC721.sol";
import "./contracts/access/Ownable.sol";

contract MyNFT is ERC721, Ownable {
    uint256 public totalSupply = 1000;
    uint256 private _tokenIdCounter = 1;
    mapping(uint256 => string) private _tokenURIs;

    constructor() ERC721("MyNFT", "MNFT") {}

    function _setTokenURI(uint256 tokenId, string memory tokenURI) internal {
        _tokenURIs[tokenId] = tokenURI;
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        return _tokenURIs[tokenId];
    }

    function mint(address to, string memory metadataURI) public onlyOwner {
        require(_tokenIdCounter <= totalSupply, "Max supply reached");
        _safeMint(to, _tokenIdCounter);
        _setTokenURI(_tokenIdCounter, metadataURI);
        _tokenIdCounter++;
    }
}
"""

install_solc("0.8.0")
set_solc_version("0.8.0")
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"MyNFT.sol": {"content": erc721_contract}},
    "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
})
abi = compiled_sol['contracts']['MyNFT.sol']['MyNFT']['abi']
bytecode = compiled_sol['contracts']['MyNFT.sol']['MyNFT']['evm']['bytecode']['object']

# 5. 部署合约
MyNFT = w3.eth.contract(abi=abi, bytecode=bytecode)
tx = MyNFT.constructor().build_transaction({
    'from': my_address,
    'nonce': w3.eth.get_transaction_count(my_address),
    'gas': w3.eth.estimate_gas({'from': my_address, 'to': '', 'data': bytecode}),
    'gasPrice': w3.eth.gas_price,
})
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"{YELLOW}{BOLD}🎉 合约部署中... 交易哈希: 0x{tx_hash.hex()}{RESET}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
nft_contract_address = receipt.contractAddress
print(f"{GREEN}{BOLD}✅ 合约部署成功！地址: {nft_contract_address}{RESET}")

# 6. 调用 mint 方法铸造并转移 NFT
nft_contract = w3.eth.contract(address=nft_contract_address, abi=abi)
vitalik_address = w3.to_checksum_address("0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
nft_metadata_url = "ipfs://bafybeihrww2kdslgk6bfrbc6d7fx7c5bavzey57aj5pokvw3je3xtcxm3i/5493.json"
tx = nft_contract.functions.mint(vitalik_address, nft_metadata_url).build_transaction({
    'from': my_address,
    'nonce': w3.eth.get_transaction_count(my_address),
    'gas': w3.eth.estimate_gas({'from': my_address, 'to': nft_contract_address, 'data': nft_contract.encodeABI(fn_name='mint', args=[vitalik_address, nft_metadata_url])}),
    'gasPrice': w3.eth.gas_price,
})
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"{GREEN}{BOLD}🎉 NFT 成功转移至 V 神地址！交易哈希: 0x{tx_hash.hex()}{RESET}")