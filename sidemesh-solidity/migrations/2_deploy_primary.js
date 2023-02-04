const Register = artifacts.require("./resource/Register.sol");
const LockManager = artifacts.require("./lock/LockManager.sol");

const PrimaryTransactionManager = artifacts.require(
	"./transaction/PrimaryTransactionManager.sol"
);
const CrossChain = artifacts.require("./CrossChain.sol");

module.exports = async function (deployer) {
	await deployer.deploy(Register);

	const register = await Register.deployed();

	const lockManager = await deployer.deploy(LockManager, register.address);

	const primaryTransactionManager = await deployer.deploy(
		PrimaryTransactionManager,
		register.address,
		lockManager.address
	);

	await deployer.deploy(
		CrossChain,
		register.address,
		primaryTransactionManager.address
	);
};
