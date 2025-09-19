"""
Compute checksum for file content
"""
import hashlib

def compute_checksum(data: bytes) -> str:
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()
