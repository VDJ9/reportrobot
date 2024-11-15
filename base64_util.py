import base64

def encode_base64(credentials):
    return base64.b64encode(credentials.encode('utf-8')).decode('utf-8')