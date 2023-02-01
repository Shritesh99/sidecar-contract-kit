const SimpleStroage = artifacts.require("./SimpleStorage.sol");

module.exports = async function (deployer) {
	deployer.deploy(SimpleStroage, { overwrite: true });
};
