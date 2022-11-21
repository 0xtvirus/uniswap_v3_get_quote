from web3 import Web3, HTTPProvider
import json
from dotenv import load_dotenv
import os, math


# get keys from .env
load_dotenv()
API_KEY = os.getenv('API_KEY')

# connect rpc node
url = "https://rpc.ankr.com/eth" # public rpc node
w3 = Web3(HTTPProvider(url))
if w3.isConnected() == False:
    print("Not connected to the network")


with open("../build/contracts/IERC20Minimal.json") as fh:
    token_abi = json.load(fh)

with open('../build/contracts/IUniswapV3Factory.json') as fh:
    factory_abi = json.load(fh)

with open('../build/contracts/IUniswapV3Pool.json') as fh:
    pool_abi = json.load(fh)


def token_info(address, abi=token_abi, w3=w3):
    token = {}
    address = Web3.toChecksumAddress(address)
    contract = w3.eth.contract(address=address, abi=abi)
    token['Name'] = contract.functions.name().call()
    token['Symbol'] = contract.functions.symbol().call()
    token['Decimals'] = contract.functions.decimals().call()
    token['Contract'] = w3.toChecksumAddress(address)
    return token


def get_amount_out(token_in, token_out, amount_in, factory_addresses, fee='%0.3', secondsAgo=10, w3=w3):

    # references
    # https://github.com/stakewithus/notes/blob/main/excalidraw/uni-v3-twap-geometric-mean.png
    # https://github.com/t4sk/uniswap-v3-twap/blob/main/contracts/UniswapV3Twap.sol

    token_in = w3.toChecksumAddress(token_in)
    token_out = w3.toChecksumAddress(token_out)

    fees = {'%0.3': int(0.3 * 10000), '%0.05': int(0.05 * 10000), '%1': int(1 * 10000)}
    factory = w3.eth.contract(address=factory_addresses, abi=factory_abi["abi"])
    pool_address = factory.functions.getPool(token_in, token_out, fees[fee]).call()
    pool = w3.eth.contract(address=pool_address, abi=pool_abi["abi"])

    secondsAgos = [int(0), secondsAgo]
    token = []
    tickCumulatives, _ = pool.functions.observe(secondsAgos).call()

    i0, i1 = 0, 1
    token.append(token_info(pool.functions.token0().call(), token_abi["abi"]))
    token.append(token_info(pool.functions.token1().call(), token_abi["abi"]))


    if token_in == token[i0]['Contract']: i0,i1 = 1,0


    tickCumulativesDelta = tickCumulatives[i1] - tickCumulatives[i0]
    tick = tickCumulativesDelta / secondsAgo
    # if tickCumulativesDelta < 0 & (tickCumulativesDelta % secondsAgo != 0):
    #     math.floor(tick)

    ans = (1.0001 ** tick)
    result = ans*10**(token[i1]["Decimals"] - token[i0]["Decimals"])

    return result*amount_in, "%s %s =  %s %s"%(amount_in, token[i1]['Symbol'], result*amount_in, token[i0]['Symbol']), pool_address





if __name__ == "__main__":
    with open('./addresses.json') as fh:
        addresses = json.load(fh)
    ETH_DAI = get_amount_out(addresses["WETH"], addresses["DAI"], 1, addresses["FACTORY"])
    ETH_USDC = get_amount_out(addresses["WETH"], addresses["USDC"], 1, addresses["FACTORY"])
    ETH_USDT = get_amount_out(addresses["WETH"], addresses["USDT"], 1, addresses["FACTORY"])
    UNI_USDC = get_amount_out(addresses["UNI"], addresses["USDC"], 1, addresses["FACTORY"])
    UNI_USDT = get_amount_out(addresses["UNI"], addresses["USDT"], 1, addresses["FACTORY"])
    print(ETH_DAI)
    print(ETH_USDC)
    print(ETH_USDT)
    print(UNI_USDC)
    print(UNI_USDT)


