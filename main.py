import sys
import math
from decimal import Decimal
from typing import Any


def _string_to_any_type(
    verification_text: str, expected_type: type, err_message: str
) -> Any | None:
    """Takes a text `verification_text` and tries to cast it to a type `expected_type` and asks the user for input and returns `None` or the value casted to `expected_type` if it cant it will re ask for the input until `"q"` or `"quit"` is typed

    Args:
        verification_text:(str) The text to convert to the type of `expected_type`.
        expected_type:(type) The type to convert `verification_text` to.
        err_message:(str) The err message to display if the conversion cant work.
    Returns:
       Any: The conversion of `verification_text` to type `expected_type`
    """
    value = None

    while value is None:
        if (
            verification_text.lower().strip() == "q"
            or verification_text.lower().strip() == "quit"
        ):
            sys.exit(1)
        try:
            value = expected_type(verification_text)
        except ValueError:
            verification_text = input(err_message)
    return value


def _verify_dollar_amount(dollars: str, err_message: str):
    """Verifies the value of `dollars` is a valid currency amount with up to two decimal places

    Args:
        dollars (str): The amount in USD
        err_message (str): A Err to receive when a invalid number is typed

    Returns:
        float: amount in USD if valid number was typed
    """

    value = None
    while value is None:
        if dollars.lower().strip() == "q" or dollars.lower().strip() == "quit":
            sys.exit(1)
        try:
            dollars = Decimal(dollars)
            count_after_decimal = abs(dollars.as_tuple().exponent)
            if count_after_decimal > 2:
                dollars = input(err_message)
            else:
                value = float(dollars)
        except:
            dollars = input(err_message)
    return value


def _yes_or_no(answer: str) -> bool:
    """Helper function to return a boolean from a string

    Args:
        answer (str): the string to convert

    Returns:
        bool: whether they answer was yes
    """
    YES_WORDS = ["yes", "please", "y"]
    if answer.lower().strip() in YES_WORDS:
        print("Selected yes.")
        return True
    else:
        print("Selected no.")

        return False


def _multi_choice(
    choices: list[str], input_string: str, err_message: str, default: str | None = None
) -> str:
    """Make a choice from `choices`

    Args:
        choices (list[str]): The valid options
        input_string (str): The input from the user
        err_message (str): The err to show if `default` is not set and option is invalid
        default (str | None, optional): The default option if a invalid `input_string` is given. Defaults to None.

    Returns:
        str: The option that was selected.
    """

    output_string = None

    while output_string is None:
        input_string = input_string.strip().lower()
        if input_string == "q" or input_string == "quit":
            sys.exit(1)
        if input_string in choices:
            output_string = input_string
        elif default is not None:
            print(err_message)
            output_string = default
        else:
            input_string = input(err_message)


def main():
    pass


if __name__ == "__main__":
    main()
