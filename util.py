# The following code contains functions for string normalization and cleaning

import unicodedata
from bs4 import NavigableString
from typing import List


def normalize_str(text: str):
    """
    Replace diacritical characters and normalize the string this way.

    Args:
        text (str): String to be normalized

    Returns:
        str: Normalized version of the string
    """
    text = clean_string(text.strip())
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')


def clean_string(text: str):
    """
    Replace MS Office Special Characters from a String as well as double whitespace

    Args:
        text (str): String to be cleaned

    Returns:
        str: Cleaned string
    """
    result = ' '.join(text.split())
    result = result.replace('\r', '').replace('.', '').replace(
        '\n', ' ').replace(u'\xa0', u' ').replace(u'\xad', u'-').rstrip().lstrip()
    return result


banned_set = set([
    # No idea about this one, occurs in the dataset but has passed away before the time the dataset was made?
    # Probably another person with the same name but can't find info about them. (see #10)
    ' Ramaekers Jef',
    # Again, this person voted but was in the senate
    # No records show him being elected to the House of Representatives.
    ' Collignon Christophe',
    'Collignon Christophe',
    'Christophe Collignon',
    # This member wasn't a part of the House of Representatives
    ' Annane Jihane',
    'Annane Jihane',
    'Jihane Annane',
    # Well, the string below was added because of some format issues in https://www.dekamer.be/doc/PCRI/html/52/ip078x.html, we should solve this better (by using a RegEx)
    '(Ingevolge een technisch mankement werd de stemming van mevrouw Inge Vervotte',
    ' afwezig',
    ' opgenomen)',
    '(A la suite d’une erreur technique',
    ' le vote de Mme Inge Vervotte',
    ' absente',
    '(Om technische redenen is er geen stemming nr 2 / Pour raison technique',
    " il n'y a pas de vote n° 2)",
    '(De heer Guido De Padt heeft gestemd vanop de bank van de heer Ludo Van Campenhout',
    ' afwezig)',
    ' a été enregistré)',
    # Bogus comments
    '<![if !supportEmptyParas]> <![endif]>',
])


def is_string_banned(string: str):
    """
    Check if a string is in the banned set.

    Args:
        string (str): String to be checked

    Returns:
        bool: True if string is banned, False otherwise
    """
    return string in banned_set


def is_string_banned_or_empty(string: str):
    """
    Check if a string is in the banned set or empty.

    Args:
        string (str): String to be checked

    Returns:
        bool: True if string is banned or empty, False otherwise
    """
    return not string or is_string_banned(string)


def clean_list(list: List[any]):
    """
    Removes falsy items from a list.

    Args:
        list (List[any]): List to be cleaned

    Returns:
        List[str]: Cleaned list
    """
    return [clean_string(item) for item in list if not is_string_banned_or_empty(item)]


def go_to_p(tag: NavigableString):
    """
    Go to the nearest parent p tag of a NavigableString.

    Args:
        tag (NavigableString): NavigableString object

    Returns:
        NavigableString: Parent p tag of the given NavigableString object
    """
    while tag.name != "p":
        tag = tag.parent
    return tag