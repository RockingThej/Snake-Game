"""S2-14: login that refuses accounts an administrator has disabled."""
from auth import DbAuth
from db import get_user_by_username
from db.admin_repository import is_account_disabled


class SecureAuth(DbAuth):
    """``DbAuth`` plus the account-status check.

    The login screen shows the same "wrong username or password" message for
    a disabled account as for a wrong password, so it reveals nothing.
    """

    def login(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return False
        user = get_user_by_username(username.strip(), db_path=self.db_path)
        if user is not None and is_account_disabled(
                user["id"], db_path=self.db_path):
            return False
        return super().login(username, password)
