"""
ssl_patch.py — Must be imported FIRST in app.py and main.py.

GSK runs Zscaler SSL inspection: every outbound HTTPS connection is
re-signed by the GSK Issuing CA 1.  The Azure CLI pre-sets
REQUESTS_CA_BUNDLE to its own certifi copy which doesn't include the
GSK corporate CA, so all requests fail with CERTIFICATE_VERIFY_FAILED.

This module resolves the absolute path of gsk_ca_bundle.pem (bundled
next to this file) and forcefully sets REQUESTS_CA_BUNDLE and
SSL_CERT_FILE so both `requests` and `httpx` (used by the Anthropic
SDK) trust the GSK cert chain.
"""

import os
from pathlib import Path

_BUNDLE = Path(__file__).parent / "gsk_ca_bundle.pem"

if _BUNDLE.exists():
    bundle_path = str(_BUNDLE)
    # Override regardless of what the shell environment already has
    os.environ["REQUESTS_CA_BUNDLE"] = bundle_path
    os.environ["SSL_CERT_FILE"] = bundle_path
    # httpx (used by anthropic SDK) respects SSL_CERT_FILE automatically
else:
    import warnings
    warnings.warn(
        "gsk_ca_bundle.pem not found — SSL calls may fail on the GSK network. "
        "Run: python3 build_gsk_bundle.py",
        stacklevel=2,
    )
