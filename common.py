# Importing the Enum module from the enum package
from enum import Enum

# Defining an Enum class called Language to differentiate between the two languages used in the meetings of the parliament
class Language(Enum):
    '''
    Enum used to differentiate between the two languages used in the meetings
    of the parliament.
    '''
    NL = 0
    FR = 1

# Defining an Enum class called Choice to differentiate between the different choices made during the meetings of the parliament
class Choice(Enum):
    '''
    Enum used to differentiate between the different choices made during the meetings of the parliament
    '''
    NO = 0
    YES = 1
    ABSTENTION = 2