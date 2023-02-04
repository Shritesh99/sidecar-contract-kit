const Register = artifacts.require("./resource/Register.sol");
const LockManager = artifacts.require("./lock/LockManager.sol");

const NetworkTransactionManager = artifacts.require(
	"./transaction/NetworkTransactionManager.sol"
);
const CrossNetwork = artifacts.require("./CrossNetwork.sol");

module.exports = async function (deployer) {
	await deployer.deploy(Register);

	const register = await Register.deployed();

	const lockManager = await deployer.deploy(LockManager, register.address);

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
