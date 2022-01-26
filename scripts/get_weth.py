from webbrowser import get


from scripts.helpful_scripts import *
from brownie import interface, config, network
from web3 import Web3


def main():
    get_weth()


def get_weth():
    """
    Mints WETH by depositing ETH.
    """

    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": Web3.toWei(0.001, "ether")})
    tx.wait(1)
    print("Received 0.01 WETH")
    return tx
