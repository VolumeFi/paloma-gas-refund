from dotenv import load_dotenv
from mixpanel import Mixpanel
import os
import sentry_sdk
import sys
from api.functions import get_from_block, get_refund_list
from web3 import Web3
from eth_account import Account
from api.blockscan_api import BlockscanConnector
from web3.gas_strategies.rpc import rpc_gas_price_strategy

mp: Mixpanel

def refund_tx(w3: Web3, refund_list: dict, refund_contract_address: str, refund_contract_abi: dict, chain_name: str, account_from):
    w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
    value = 0
    address_list = []
    amount_list = []
    for receiver in refund_list:
        value += refund_list[receiver]
        address_list.append(w3.toChecksumAddress(receiver))
        amount_list.append(refund_list[receiver])
        mp.track(receiver, 'GAS_REFUND', {
                 'TYPE': chain_name, 'VALUE': refund_list[receiver]})
    if value > 0:  # this should be added. if value equals zero, we don't need to run tx.
        refund_sc = w3.eth.contract(
            address=refund_contract_address, abi=refund_contract_abi)
        nonce = w3.eth.get_transaction_count(account_from.address)
        tx_create = refund_sc.functions.refund(address_list, amount_list).build_transaction(
            {"value": value, "nonce": nonce, "from": account_from.address})
        signed_tx = w3.eth.account.sign_transaction(
            tx_create, private_key=account_from.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(
            f"Transaction successful with hash: { tx_receipt.transactionHash.hex() }")
    else:
        print('no refund needed')

def refund_eip1559_tx(w3: Web3, refund_list: dict, refund_contract_address: str, refund_contract_abi: dict, chain_name: str, account_from):
    value = 0
    address_list = []
    amount_list = []
    for receiver in refund_list:
        value += refund_list[receiver]
        address_list.append(w3.toChecksumAddress(receiver))
        amount_list.append(refund_list[receiver])
        mp.track(receiver, 'GAS_REFUND', {
                 'TYPE': chain_name, 'VALUE': refund_list[receiver]})
    if value > 0:  # this should be added. if value equals zero, we don't need to run tx.
        refund_sc = w3.eth.contract(
            address=refund_contract_address, abi=refund_contract_abi)
        nonce = w3.eth.get_transaction_count(account_from.address)
        max_priority_fee = w3.eth.max_priority_fee
        gas_price = w3.eth.gas_price * 2 + max_priority_fee
        tx_create = refund_sc.functions.refund(address_list, amount_list).build_transaction(
            {"value": value, "nonce": nonce, "from": account_from.address, "maxFeePerGas": gas_price,
             "maxPriorityFeePerGas": max_priority_fee})
        signed_tx = w3.eth.account.sign_transaction(
            tx_create, private_key=account_from.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(
            f"Transaction successful with hash: { tx_receipt.transactionHash.hex() }")
    else:
        print('no refund needed')

def bsc_refund():
    node = os.environ['BSC_NODE']
    w3 = Web3(Web3.HTTPProvider(node))
    print('check BSC node connected: ', w3.isConnected())
    private_key = os.environ['BSC_PRIVATE_KEY']
    refund_wallet = Account.from_key(private_key)
    assert refund_wallet.address == os.environ['BSC_REFUND_WALLET']
    refund_contract_address = os.environ['BSC_REFUND_CONTRACT']
    refund_contract_abi = [{"type": "function", "name": "refund", "stateMutability": "payable", "inputs": [
        {"name": "receivers", "type": "address[]"}, {"name": "amounts", "type": "uint256[]"}], "outputs": []}]
    blockscanner = BlockscanConnector(
        os.environ['BSCSCAN_API_PREAMBLE'], os.environ['BSCSCAN_API_KEY'])
    from_block = get_from_block(
        blockscanner, refund_contract_address, refund_wallet.address)
    compass_evm = os.environ['BSC_COMPASS_EVM']
    refund_list = get_refund_list(blockscanner, compass_evm, from_block)
    refund_tx(w3, refund_list, refund_contract_address,
              refund_contract_abi, 'BNB', refund_wallet)


def eth_refund():
    node = os.environ['ETH_NODE']
    w3 = Web3(Web3.HTTPProvider(node))
    print('check ETH node connected: ', w3.isConnected())
    private_key = os.environ['ETH_PRIVATE_KEY']
    refund_wallet = Account.from_key(private_key)
    assert refund_wallet.address == os.environ['ETH_REFUND_WALLET']
    refund_contract_address = os.environ['ETH_REFUND_CONTRACT']
    refund_contract_abi = [{"type": "function", "name": "refund", "stateMutability": "payable", "inputs": [
        {"name": "receivers", "type": "address[]"}, {"name": "amounts", "type": "uint256[]"}], "outputs": []}]
    blockscanner = BlockscanConnector(
        os.environ['ETHERSCAN_API_PREAMBLE'], os.environ['ETHERSCAN_API_KEY'])
    from_block = get_from_block(
        blockscanner, refund_contract_address, refund_wallet.address)
    compass_evm = os.environ['ETH_COMPASS_EVM']
    refund_list = get_refund_list(blockscanner, compass_evm, from_block)
    refund_eip1559_tx(w3, refund_list, refund_contract_address,
              refund_contract_abi, 'ETH', refund_wallet)


def polygon_refund():
    node = os.environ['POLYGON_NODE']
    w3 = Web3(Web3.HTTPProvider(node))
    print('check POLYGON node connected: ', w3.isConnected())
    private_key = os.environ['POLYGON_PRIVATE_KEY']
    refund_wallet = Account.from_key(private_key)
    assert refund_wallet.address == os.environ['POLYGON_REFUND_WALLET']
    refund_contract_address = os.environ['POLYGON_REFUND_CONTRACT']
    refund_contract_abi = [{"type": "function", "name": "refund", "stateMutability": "payable", "inputs": [
        {"name": "receivers", "type": "address[]"}, {"name": "amounts", "type": "uint256[]"}], "outputs": []}]
    blockscanner = BlockscanConnector(
        os.environ['POLYGONSCAN_API_PREAMBLE'], os.environ['POLYGONSCAN_API_KEY'])
    from_block = get_from_block(
        blockscanner, refund_contract_address, refund_wallet.address)
    compass_evm = os.environ['POLYGON_COMPASS_EVM']
    refund_list = get_refund_list(blockscanner, compass_evm, from_block)
    refund_eip1559_tx(w3, refund_list, refund_contract_address,
              refund_contract_abi, 'POLYGON', refund_wallet)


def main():
    load_dotenv()
    global mp
    mp = Mixpanel(os.environ['MIXPANEL_TOKEN'])
    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], traces_sample_rate=1.0)
    current_dir = os.getcwd()
    sys.path.insert(1, os.path.abspath(os.path.join(current_dir, '../../')))
    bsc_refund()
    eth_refund()
#    polygon_refund()

if __name__ == "__main__":
    main()
