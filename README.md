## 一键部署合约

### 克隆仓库并运行部署脚本

```bash
git clone https://github.com/blockchain-src/deploy_contracts.git
cd deploy_contracts
chmod +x deploy.sh
./deploy.sh
```

### ====代码整体流程====

1. **检查并安装必要的软件包**
   - 根据不同的操作系统（Linux、macOS、Windows）安装所需的软件包。

2. **检查并安装 Python 库**
   - 创建或激活 Python 虚拟环境（venv）。
   - 在虚拟环境中检查并安装必要的 Python 依赖项

3. **用户输入私钥**
   - 确保私钥以 `0x` 开头，并且长度正确。

4. **连接 Web3**
   - 通过 Monad 测试网的 RPC 端点连接 Web3。

5. **获取钱包地址和账户余额**
   - 获取与私钥对应的钱包地址。
   - 检查账户余额是否足够支付 Gas 费用。

6. **编写并编译 Solidity 合约**
   - 编写 ERC-20 代币合约。
   - 代币名称：`HOLD`
   - 总供应量：10 亿。

7. **部署合约**
   - 将合约部署到区块链上。

8. **执行代币转账**
   - 向 Vitalik Buterin 的地址 `0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045` 转账 1000 `HODL` 代币。

### 注意事项

- 确保私钥的安全性，不要在公共场合暴露私钥。
- 确保账户余额足够支付 Gas 费用，否则部署和转账操作将失败。
- 部署合约时，请确认网络连接正常，避免因网络问题导致部署失败。

### 参考

- [Monad 测试网 RPC 端点](https://monad-testnet-rpc.example.com)
- [Solidity 官方文档](https://soliditylang.org/docs/)
- [Web3.js 官方文档](https://web3js.readthedocs.io/)
---
