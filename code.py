from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64

vapid = Vapid()
vapid.generate_keys()

# Export public key (required by browser)
public_key_bytes = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint,
)

public_key = base64.urlsafe_b64encode(public_key_bytes).decode("utf-8")

# Export private key (server-side only)
private_key_bytes = vapid.private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

private_key = base64.urlsafe_b64encode(private_key_bytes).decode("utf-8")

print("PUBLIC KEY:\n", public_key)
print("\nPRIVATE KEY:\n", private_key)
