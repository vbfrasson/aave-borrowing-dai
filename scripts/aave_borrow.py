from xmlrpc.client import _datetime_type
from brownie import config, accounts, network, interface
from scripts.helpful_scripts import *
from scripts.get_weth import *
from web3 import Web3

AMOUNT = Web3.toWei(0.001, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    print(lending_pool)
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, AMOUNT, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Lets borrow some $$$")
    # DAI/ETH Price Feed
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    # borrowable eth -> borrowable dai * 95%(so we are not liquidated)
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_dai_to_borrow}")
    dai_address = config["networks"][network.show_active()]["dai_token_address"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("DAI has been borrowed\n", get_borrowable_data(lending_pool, account))


def get_asset_price(_price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(_price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    latest_price = Web3.fromWei(latest_price, "ether")  # converts Wei to ETH
    print(f"DAI/ETH price is {latest_price}")
    return float(latest_price)


def get_borrowable_data(_lending_pool, _account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = _lending_pool.getUserAccountData(_account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have a total of {total_collateral_eth} worth of ETH deposited")
    print(f"You have a total of {total_debt_eth} worth of ETH borrowed")
    print(f"You can borrow {available_borrow_eth} worth of ETH")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(_amount, _spender, _erc20_address, _account):
    print("Approving ERC20 Token")
    erc20 = interface.IERC20(_erc20_address)
    tx = erc20.approve(_spender, _amount, {"from": _account})
    tx.wait(1)
    print("ERC20 Approved")
    return tx


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
