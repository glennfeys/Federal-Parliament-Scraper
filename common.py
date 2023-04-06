# This code defines two enums, Language and Choice, used to differentiate between languages and voting choices in parliament meetings.

from enum import Enum

class Language(Enum):
    '''
    Enum used to differentiate between the two languages used in the meetings
    of the parliament.
    '''
    NL = 0 # Represents Dutch language
    FR = 1 # Represents French language

class Choice(Enum):
    '''
    Enum used to differentiate between the three voting choices in the meetings
    of the parliament: no, yes, and abstention.
    '''
    NO = 0 # Represents a vote of "no"
    YES = 1 # Represents a vote of "yes"
    ABSTENTION = 2 # Represents a vote of "abstention" or not voting.