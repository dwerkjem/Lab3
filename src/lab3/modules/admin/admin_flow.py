import questionary


class Admin:
    def __init__(self):
        pass

    def auth() -> bool:
        """Authenticates the admin

        Returns:
            bool: whether they are authorized or not.
        """
        password = questionary.password(
            "Verify with a password\n  The password is `Password123` for demo purposes"
        ).ask()
        if (
            password == "Password123"
        ):  # in production this would be encrypted and read from a .env file
            questionary.print("Welcome Admin", style="bold fg:ansigreen")
            return True
        else:
            questionary.print("You are unauthorized", style="bold fg:ansired")
            return False
