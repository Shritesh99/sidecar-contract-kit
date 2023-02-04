const truffleAssert = require("truffle-assertions");
const web3 = require("web3");
const CrossNetwork = artifacts.require("./CrossNetwork.sol");

contract("CrossNetwork", (accounts) => {
	let account;
	let primaryNetworkId, primaryNetworkName, primaryNetworkUrl;
	let networkId,
		networkName,
		networkUrl,
		invocationId,
		contractAddress,
		funcSign,
		args;
	let txId;
	// let crossNetworkInstance;
	// before(async () => {
	account = accounts[0];

	primaryNetworkId = "primaryNetworkId";
	primaryNetworkName = "besu";
	primaryNetworkUrl = "http://127.0.0.1:7545";

	networkId = "networkId";
	networkName = "fabric";
	networkUrl = "http://127.0.0.1:7545";
	invocationId = "invocationId";
	contractAddress = "0xcFFB419EA4855c1FDa876119aBA3D062d7FC31D7";
	funcSign = "set(uint256)";

	args = 12;

	txId = "test";
	// });
	it("DoNetwork", async () => {
		const crossNetworkInstance = await CrossNetwork.deployed();
		await crossNetworkInstance.registerPrimaryNetwork(
			primaryNetworkId,
			primaryNetworkName,
			primaryNetworkUrl,
			{ from: account }
		);

		await crossNetworkInstance.registerNetwork(
			networkId,
			networkName,
			networkUrl,
			invocationId,
			contractAddress,
			funcSign,
			{ from: account }
		);

		const result = await crossNetworkInstance.doNetwork(
			txId,
			primaryNetworkId,
			networkId,
			invocationId,
			web3.utils.toHex(args),
			{ from: account }
		);
		truffleAssert.eventEmitted(
			result,
			"NetworkTxStatus",
			(ev) => {
				assert(ev.txId === txId, "Triggered Prepare Network Tx");
				return true;
			},
			"Event: Prepare Network Tx"
		);
	});
	it("ConfirmDoNetwork", async () => {
		const crossNetworkInstance = await CrossNetwork.deployed();
		const result = await crossNetworkInstance.confirmDoNetwork(txId);
		await truffleAssert.eventEmitted(
			result,
			"ConfirmNetworkTransaction",
			(ev) => {
				assert(ev.txId === txId, "Triggered Prepare Network Tx");
				return true;
			},
			"Event: Confirm Network Tx"
		);
	});
});
