import os
import base64
from cryptography.fernet import Fernet
from kubernetes import client, config

# --- CONFIGURATION ---
NAMESPACE = "default"
SECRET_NAME = "miso-admin-key"
KEY_FIELD = "fernet-key"

def get_k8s_client():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            return None
    return client.CoreV1Api()

def get_or_create_key():
    v1 = get_k8s_client()
    # Fallback for local testing
    if not v1:
        return Fernet.generate_key()

    try:
        # 1. READ EXISTING
        secret = v1.read_namespaced_secret(SECRET_NAME, NAMESPACE)
        key_b64 = secret.data.get(KEY_FIELD)
        if key_b64:
            print(f"✅ Loaded persistent Master Key from Secret: {SECRET_NAME}")
            return base64.b64decode(key_b64)
    except client.exceptions.ApiException as e:
        if e.status != 404:
            raise e 

    # 2. CREATE NEW
    print(f"⚠️ No key found. Generating NEW Master Key...")
    key = Fernet.generate_key()
    secret_body = client.V1Secret(
        metadata=client.V1ObjectMeta(name=SECRET_NAME),
        string_data={KEY_FIELD: key.decode()}
    )
    try:
        v1.create_namespaced_secret(NAMESPACE, secret_body)
        print(f"💾 Saved new Master Key to Kubernetes Secret: {SECRET_NAME}")
    except client.exceptions.ApiException as e:
        if e.status == 409: 
             secret = v1.read_namespaced_secret(SECRET_NAME, NAMESPACE)
             return base64.b64decode(secret.data[KEY_FIELD])
        else:
            raise e
    return key

if __name__ == "__main__":
    key = get_or_create_key()
    print("Key logic check complete.")
