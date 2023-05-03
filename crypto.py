import base64
import hashlib
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def encrypt(passphrase, filepath):
    key = derive_key(passphrase, generate_salt=True)
    f = Fernet(key)

    with open(filepath, "rb") as file:
        plaintext = file.read()  # binary read

    with open(filepath, "wb") as file:
        file.write(f.encrypt(plaintext))  # binary write
        return True


def decrypt(passphrase, filepath):
    f = Fernet(derive_key(passphrase))

    with open(filepath, "rb") as file:
        encrypted = file.read()

    plaintext = f.decrypt(encrypted)
    with open(filepath, "wb") as file:
        file.write(plaintext)


def derive_key(passphrase, generate_salt=False):
    salt = SaltManager(generate_salt)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.get(),
        iterations=1000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase))


def hash_string(string):
    hash_object = hashlib.sha256(string.encode())
    return hash_object.hexdigest()


def check_hashes(string, hash):
    hash_object = hashlib.sha256(string.encode())
    hash2 = hash_object.hexdigest()
    if hash2 == hash:
        return True
    else:
        return False


class SaltManager(object):
    def __init__(self, generate, path=".salt"):
        self.generate = generate
        self.path = path

    def get(self):
        if self.generate:
            return self._generate_and_store()
        return self._read()

    def _generate_and_store(self):
        salt = os.urandom(16)
        with open(self.path, "wb") as f:
            f.write(salt)
        return salt

    def _read(self):
        with open(self.path, "rb") as f:
            return f.read()