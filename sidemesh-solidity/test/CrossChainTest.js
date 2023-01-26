// const truffleAssert = require("truffle-assertions");
// const web3 = require("web3");
// const CrossChain = artifacts.require("./CrossChain.sol");

// contract("CrossChain", (accounts) => {
// 	let account;
// 	let primaryNetworkId, primaryNetworkName, primaryNetworkUrl;
// 	let networkId,
// 		networkName,
// 		networkUrl,
// 		invocationId,
// 		contractAddress,
// 		funcSign,
// 		args;
// 	let txId;
// 	let crossChainInstance;
// 	before(async () => {
// 		account = accounts[0];

// 		primaryNetworkId = "primaryNetworkId";
// 		primaryNetworkName = "besu";
// 		primaryNetworkUrl = "http://127.0.0.1:7545";

// 		networkId = "networkId";
// 		networkName = "fabric";
// 		networkUrl = "http://127.0.0.1:7545";
// 		invocationId = "invocationId";
// 		contractAddress = "0xcFFB419EA4855c1FDa876119aBA3D062d7FC31D7";
// 		funcSign = "set(uint256)";

// 		args = 12;

// 		txId = "test";

// 		crossChainInstance = await CrossChain.deployed();
// 	});
// 	it("DoCross", async () => {
// 		await crossChainInstance.registerPrimaryNetwork(
// 			primaryNetworkId,
// 			primaryNetworkName,
// 			primaryNetworkUrl,
// 			{ from: account }
// 		);
// 		await crossChainInstance.registerNetwork(
// 			networkId,
// 			networkName,
// 			networkUrl,
// 			invocationId,
// 			contractAddress,
// 			funcSign,
// 			{ from: account }
// 		);

// 		const result = await crossChainInstance.doCross(
// 			txId,
// 			networkId,
// 			invocationId,
// 			web3.utils.toHex(args),
// 			{ from: account }
// 		);

// 		await crossChainInstance.changeStatus(txId, 2);
// 		await crossChainInstance.changeStatus(txId, 3);

// 		await truffleAssert.eventEmitted(
// 			result,
// 			"PreparePrimaryTransaction",
// 			(ev) => {
// 				assert(ev.txId === txId, "Triggered Prepare Primary Tx");
// 				return true;
// 			},
// 			"Event: Prepare Primary Tx"
// 		);
// 	});
// 	it("ConfirmDoCross", async () => {
// 		const result = await crossChainInstance.confirmDoCross(txId);
// 		truffleAssert.eventEmitted(
// 			result,
// 			"PrimaryTxStatus",
// 			(ev) => {
// 				assert(ev.txId === txId, "Triggered Confirm Primary Tx");
// 				return true;
// 			},
// 			"Event: Confirm Primary Tx"
// 		);
// 	});
// });
