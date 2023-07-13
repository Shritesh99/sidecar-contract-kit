# Sidemesh Solidity Contract Kit

```
truffle compile
```

```
truffle publish
```

```

ff deploy ethereum dev Register.json
ff deploy ethereum dev LockManager.json 0x5f55f168d5c31cfc2d998d9175b99809dc9898ae

ff deploy ethereum dev PrimaryTransactionManager.json 0x5f55f168d5c31cfc2d998d9175b99809dc9898ae 0x6aaf6916a4eea2b1bd1d800dec9099938b482862

ff deploy ethereum dev CrossChain.json 0x5f55f168d5c31cfc2d998d9175b99809dc9898ae 0x2167d9f8b0db1962c789027d50cc7cf90b26c083

ff deploy ethereum dev NetworkTransactionManager.json

ff deploy etherum dev CrossNetwork.json

```

```
// registerPrimaryNetwork
{
  "input": {
    "id": "1",
    "name": "besu-1",
    "url": "http://192.168.0.214:5001"
  }
}
// registerNetwork
{
  "input": {
    "contractAddress": "0x29b834ea8231c73c7afe0b383dc520256a0bc6a0",
    "functionSignature": "set(bytes)",
    "invocationId": "iv-1",
    "name": "Set",
    "networkId": "2",
    "url": "http://192.168.0.162:5001"
  }
}
// doCross & doNetwork
{
  "input": {
    "args": "10",
    "invocationId": "iv-1",
    "networkId": "2",
    "primaryNetworkId": "1",
    "txId": "aaa"
  }
}
// confirm
{
  "input": {
    "txId": "aaa"
  }
}
// status
{
  "input": {
    "_status": "string",
    "txId": "aaa"
  }
}
```
