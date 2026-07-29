"""
ssl_patch.py — Import FIRST in app.py and main.py.

Some corporate networks run TLS-inspecting proxies that re-sign every outbound
HTTPS connection with an internal CA. Tools that pin their own certifi bundle
(e.g. the Azure CLI) will then fail with CERTIFICATE_VERIFY_FAILED.

If you are behind such a proxy, point this module at your corporate CA bundle
by either:
  • setting the CORP_CA_BUNDLE environment variable to the .pem path, or
  • placing a file named `corporate_ca_bundle.pem` next to this file.

When a bundle is found, REQUESTS_CA_BUNDLE and SSL_CERT_FILE are set so both
`requests` and `httpx` trust the corporate certificate chain. If no bundle is
present, this module is a no-op and normal system trust is used.
"""

import os
from pathlib import Path

_bundle = os.getenv("CORP_CA_BUNDLE") or str(
    Path(__file__).parent / "corporate_ca_bundle.pem")

if Path(_bundle).exists():
    os.environ["REQUESTS_CA_BUNDLE"] = _bundle
    os.environ["SSL_CERT_FILE"] = _bundle
