# .onion vanity generator in python
# a 16/32 intel xeon cpu with like 2-3ghz does about 3.2million .onion generations per 14.6~ seconds which is around 12-14m~ .onions per minute

import base64
import multiprocessing
import os
import json
import binascii
from nacl import signing
from sha3 import sha3_256

class Ed25519KeyGen:
    def __init__(self):
        self.private_key = None
        self.public_key = None

    def generate_keys(self):
        self.private_key = signing.SigningKey.generate()
        self.public_key = self.private_key.verify_key

    def encode_public_key(self, target_string):
        checksum_bytes = b".onion checksum" + bytes(self.public_key) + b"\x03"
        checksum = sha3_256(checksum_bytes).digest()
        onion_address_bytes = bytes(self.public_key) + checksum[:2] + b"\x03"
        onion_address = base64.b32encode(onion_address_bytes).decode('utf-8').lower()
        
        if onion_address.startswith(target_string):
            self.onion_address = f'{onion_address}.onion'
            print(f"Found a matching .onion: {self.onion_address}")
            self.save_keys()
        
        return onion_address.lower()

    def save_keys(self):
        onion_directory = os.path.join('keys', self.onion_address)

        if not os.path.exists(onion_directory):
            os.makedirs(onion_directory)

        # Save private key as binary
        with open(os.path.join(onion_directory, 'ed25519_private_key.bin'), 'wb') as f:
            f.write(bytes(self.private_key))

        # Save public key as binary
        with open(os.path.join(onion_directory, 'ed25519_public_key.bin'), 'wb') as f:
            f.write(bytes(self.public_key))

        # Save onion address as hostname
        with open(os.path.join(onion_directory, 'hostname.txt'), 'w') as f:
            f.write(self.onion_address)

def generate_infinite_keys(global_counter, worker_id, target_string):
    key_gen = Ed25519KeyGen()
    local_counter = 0
    while True:
        for _ in range(10000):  # Adjust the batch size as needed
            key_gen.generate_keys()
            key_gen.encode_public_key(target_string=target_string)
            local_counter += 1

        with global_counter.get_lock():
            global_counter.value += local_counter
        local_counter = 0

        if worker_id == 0:
            print(f"Total keys generated: {global_counter.value}")

if __name__ == "__main__":
    global_counter = multiprocessing.Value('i', 0)
    cpu_count = os.cpu_count()

    processes = []
    for i in range(cpu_count):
        process = multiprocessing.Process(target=generate_infinite_keys, args=(global_counter, i))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
