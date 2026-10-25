"""Generates a VAPID key pair for Web Push (M6, F-05).

Pure local key generation -- no external account or service needed, unlike
the Supabase setup. Run once:

    cd backend && .venv/bin/python scripts/generate_vapid_keys.py

then paste the two printed lines into backend/.env.
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid.utils import b64urlencode


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_raw = private_key.private_numbers().private_value.to_bytes(32, "big")
    public_raw = public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

    print(f"VAPID_PUBLIC_KEY={b64urlencode(public_raw)}")
    print(f"VAPID_PRIVATE_KEY={b64urlencode(private_raw)}")


if __name__ == "__main__":
    main()
