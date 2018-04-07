import json
import logging

from indy import wallet, did, IndyError
from aiohttp import web
from secretsharing import PlaintextToHexSecretSharer

POOL_NAME = 'default_pool'
WALLET_NAME = 'identity_wallet'
logging.getLogger().setLevel(logging.DEBUG)


class IndyProxyServer(web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_routes([
            web.post('/create_identity', self._create_identity),
            web.post('/secret_sharding', self._secret_sharding),
            web.post('/secret_recovery', self._secret_recovery),
        ])
        self._wallet_handle = None
        self._secret_sharer = PlaintextToHexSecretSharer()

    async def _create_identity(self, request):
        try:
            logging.debug('Creating identity wallet')
            await wallet.create_wallet(POOL_NAME, WALLET_NAME, None, None, None)
            logging.debug('Opening identity wallet')
            self._wallet_handle = await wallet.open_wallet(WALLET_NAME, None, None)
            logging.debug('Generating DID and Verkey')
            new_did, new_verkey = await did.create_and_store_my_did(self._wallet_handle, "{}")
        except IndyError as e:
            logging.error(f'Error while creating identity. Exception: {e}')
            return web.Response(status=500)

        response = {
            'did': new_did,
            'verkey': new_verkey,
        }
        return web.Response(body=json.dumps(response))

    async def _secret_sharding(self, request):
        try:
            request_data = await request.json()
            verkey = request_data['verkey']
            logging.debug('Getting signing key')
            signingkey = await did.get_signing_key(self._wallet_handle, verkey)
            shards = self._secret_sharer.split_secret(signingkey, 2, 3)
        except Exception as e:
            logging.error(f'Error while sharding secret. Exception: {e}')
            return web.Response(status=500)

        response = {
            'shards': shards,
        }
        return web.Response(body=json.dumps(response))

    async def _secret_recovery(self, request):
        try:
            request_data = await request.json()
            # shards = [shard.encode() for shard in request_data['shards']]
            shards = request_data['shards']
            logging.debug('Recovering secret')
            secret = self._secret_sharer.recover_secret(shards)
        except Exception as e:
            logging.error(f'Error while recovering secret. Exception: {e}')
            return web.Response(status=500)

        response = {
            'secret': secret,
        }
        return web.Response(body=json.dumps(response))





if __name__ == '__main__':
    proxy = IndyProxyServer()
    web.run_app(proxy)