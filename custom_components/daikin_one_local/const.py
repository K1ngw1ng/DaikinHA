from datetime import timedelta

DOMAIN = "daikin_one_local"

# The docs show both port 80 (curl examples) and 8081 (discovery section).
DEFAULT_PORT = 8081

# The docs give no polling limit.
SCAN_INTERVAL = timedelta(seconds=30)
REQUEST_TIMEOUT = 10
