import requests
import curlify
import json

def json_decoder(response):
    try:
        return response.json()
    except json.JSONDecodeError:
        return response


class APIRequest:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, endpoint=None, params=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        print(curlify.to_curl(response.request))
        return json_decoder(response)

    def post(self, endpoint=None, data=None, json=None, headers=None):
        url = f"{self.base_url}"
        if endpoint:
            url = f"{self.base_url}/{endpoint}"
        
        response = requests.post(url, data=data, json=json, headers=headers)
        print(curlify.to_curl(response.request)) # remove print statement
        response.raise_for_status()
        return json_decoder(response)

    def put(self, endpoint=None, data=None, json=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.put(url, data=data, json=json, headers=headers)
        response.raise_for_status()
        print(curlify.to_curl(response.request))
        return json_decoder(response)

    def delete(self, endpoint=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        print(curlify.to_curl(response.request))
        return json_decoder(response)

