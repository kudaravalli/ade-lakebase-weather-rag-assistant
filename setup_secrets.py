"""
One-time setup script: stores Lakebase connection information
for the Weather Service application.

Usage:
    python setup_secrets.py
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace

import getpass

w = WorkspaceClient()

# Uncomment once if the scope does not exist:
w.secrets.create_scope(
    scope="database"
)

w.secrets.put_secret(
    scope="database",
    key="lakebase-url",
    string_value=getpass.getpass(
        "Paste your Lakebase URL: "
    ),
)

w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)

print("Lakebase secret configured successfully.")

