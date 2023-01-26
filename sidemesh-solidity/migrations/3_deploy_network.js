const Utils = artifacts.require("./lib/Utils.sol");
const Constants = artifacts.require("./lib/Constants.sol");

const Register = artifacts.require("./resource/Register.sol");
const LockManager = artifacts.require("./lock/LockManager.sol");

const NetworkTransactionManager = artifacts.require(
	"./transaction/NetworkTransactionManager.sol"
);
const CrossNetwork = artifacts.require("./CrossNetwork.sol");

module.exports = async function (deployer) {
	await deployer.deploy(Utils, { overwrite: false });
	await deployer.deploy(Constants, { overwrite: false });

	await deployer.link(Utils, Register);
	await deployer.link(Constants, Register);
	const register = await deployer.deploy(Register);

	await deployer.link(Utils, LockManager);
	await deployer.link(Constants, LockManager);
	const lockManager = await deployer.deploy(LockManager, register.address);

	await deployer.link(Utils, NetworkTransactionManager);
	await deployer.link(Constants, NetworkTransactionManager);
	const networkTransactionManager = await deployer.deploy(
		NetworkTransactionManager,
		register.address,
		lockManager.address
	);

	await deployer.deploy(
		CrossNetwork,
		register.address,
		networkTransactionManager.address
	);
};