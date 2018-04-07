import requests


def main():
    resp = requests.post('http://localhost:8080/create_identity')
    resp_data = resp.json()
    verkey = resp_data['verkey']
    print(f'Got verkey: {verkey}')

    resp = requests.post('http://localhost:8080/secret_sharding', json={'verkey': verkey})
    resp_data = resp.json()
    shards = resp_data['shards']
    print(f'Got shards: {shards}')

    resp = requests.post('http://localhost:8080/secret_recovery', json={'shards': [shards[1], shards[2]]})
    resp_data = resp.json()
    secret = resp_data['secret']
    print(f'Got secret: {secret}')


if __name__ == '__main__':
    main()