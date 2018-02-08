# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange
from ccxt.base.errors import ExchangeError


class bxinth (Exchange):

    def describe(self):
        return self.deep_extend(super(bxinth, self).describe(), {
            'id': 'bxinth',
            'name': 'BX.in.th',
            'countries': 'TH',  # Thailand
            'rateLimit': 1500,
            'has': {
                'CORS': False,
                'fetchTickers': True,
                'fetchOpenOrders': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766412-567b1eb4-5ed7-11e7-94a8-ff6a3884f6c5.jpg',
                'api': 'https://bx.in.th/api',
                'www': 'https://bx.in.th',
                'doc': 'https://bx.in.th/info/api',
            },
            'api': {
                'public': {
                    'get': [
                        '',  # ticker
                        'options',
                        'optionbook',
                        'orderbook',
                        'pairing',
                        'trade',
                        'tradehistory',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'biller',
                        'billgroup',
                        'billpay',
                        'cancel',
                        'deposit',
                        'getorders',
                        'history',
                        'option-issue',
                        'option-bid',
                        'option-sell',
                        'option-myissue',
                        'option-mybid',
                        'option-myoptions',
                        'option-exercise',
                        'option-cancel',
                        'option-history',
                        'order',
                        'withdrawal',
                        'withdrawal-history',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'taker': 0.25 / 100,
                    'maker': 0.25 / 100,
                },
            },
        })

    async def fetch_markets(self):
        markets = await self.publicGetPairing()
        keys = list(markets.keys())
        result = []
        for p in range(0, len(keys)):
            market = markets[keys[p]]
            id = str(market['pairing_id'])
            base = market['secondary_currency']
            quote = market['primary_currency']
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            symbol = base + '/' + quote
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': market,
            })
        return result

    def common_currency_code(self, currency):
        # why would they use three letters instead of four for currency codes
        if currency == 'DAS':
            return 'DASH'
        if currency == 'DOG':
            return 'DOGE'
        return currency

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privatePostBalance()
        balance = response['balance']
        result = {'info': balance}
        currencies = list(balance.keys())
        for c in range(0, len(currencies)):
            currency = currencies[c]
            code = self.common_currency_code(currency)
            account = {
                'free': float(balance[currency]['available']),
                'used': 0.0,
                'total': float(balance[currency]['total']),
            }
            account['used'] = account['total'] - account['free']
            result[code] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        orderbook = await self.publicGetOrderbook(self.extend({
            'pairing': self.market_id(symbol),
        }, params))
        return self.parse_order_book(orderbook)

    def parse_ticker(self, ticker, market=None):
        timestamp = self.milliseconds()
        symbol = None
        if market:
            symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': None,
            'low': None,
            'bid': float(ticker['orderbook']['bids']['highbid']),
            'ask': float(ticker['orderbook']['asks']['highbid']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float(ticker['last_price']),
            'change': float(ticker['change']),
            'percentage': None,
            'average': None,
            'baseVolume': float(ticker['volume_24hours']),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_tickers(self, symbols=None, params={}):
        await self.load_markets()
        tickers = await self.publicGet(params)
        result = {}
        ids = list(tickers.keys())
        for i in range(0, len(ids)):
            id = ids[i]
            ticker = tickers[id]
            market = self.markets_by_id[id]
            symbol = market['symbol']
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        tickers = await self.publicGet(self.extend({
            'pairing': market['id'],
        }, params))
        id = str(market['id'])
        ticker = tickers[id]
        return self.parse_ticker(ticker, market)

    def parse_trade(self, trade, market):
        timestamp = self.parse8601(trade['trade_date'])
        return {
            'id': trade['trade_id'],
            'info': trade,
            'order': trade['order_id'],
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': trade['trade_type'],
            'price': float(trade['rate']),
            'amount': float(trade['amount']),
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetTrade(self.extend({
            'pairing': market['id'],
        }, params))
        return self.parse_trades(response['trades'], market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        response = await self.privatePostOrder(self.extend({
            'pairing': self.market_id(symbol),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))
        return {
            'info': response,
            'id': str(response['order_id']),
        }

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        pairing = None  # TODO fixme
        return await self.privatePostCancel({
            'order_id': id,
            'pairing': pairing,
        })

    async def parse_order(self, order, market=None):
        side = self.safe_string(order, 'order_type')
        symbol = None
        if market is None:
            marketId = self.safe_string(order, 'pairing_id')
            if marketId is not None:
                if marketId in self.markets_by_id:
                    market = self.markets_by_id[marketId]
        if market is not None:
            symbol = market['symbol']
        timestamp = self.parse8601(order['date'])
        price = self.safe_float(order, 'rate')
        amount = self.safe_float(order, 'amount')
        return {
            'info': order,
            'id': order['order_id'],
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': price,
            'amount': amount,
        }

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        request = {}
        market = None
        if symbol is not None:
            market = self.market(symbol)
            request['pairing'] = market['id']
        response = self.privatePostGetorders(self.extend(request, params))
        orders = self.parse_orders(response['orders'], market, since, limit)
        return self.filter_orders_by_symbol(orders, symbol)

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/'
        if path:
            url += path + '/'
        if params:
            url += '?' + self.urlencode(params)
        if api == 'private':
            self.check_required_credentials()
            nonce = self.nonce()
            auth = self.apiKey + str(nonce) + self.secret
            signature = self.hash(self.encode(auth), 'sha256')
            body = self.urlencode(self.extend({
                'key': self.apiKey,
                'nonce': nonce,
                'signature': signature,
                # twofa: self.twofa,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        if api == 'public':
            return response
        if 'success' in response:
            if response['success']:
                return response
        raise ExchangeError(self.id + ' ' + self.json(response))
