from util import clean_string, is_string_banned_or_empty
from bs4 import NavigableString
from typing import List
import activity
from common import Choice


class Vote:
    """
    This function initializes a Vote object with the given parameters.
    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        yes (int): Number of yes votes
    Returns:
        None
    """
    def __init__(self, meeting_topic, vote_number: int, yes: int):
        self.meeting = meeting_topic.meeting
        self.meeting_topic = meeting_topic
        self.vote_number = vote_number
        self.yes = yes
        self.unsure = False


class GenericVote(Vote):
    """A Vote represents a single vote in a meeting.
    """

    def __init__(self, meeting_topic, vote_number: int, yes: int, no: int, abstention: int):
        """A Vote represents a single vote in a meeting.
        Args:
            meeting_topic (MeetingTopic): The meeting topic
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            yes (int): Number of yes votes
            no (int): Number of no votes
            abstention (int): Number of abstentions
        """
        Vote.__init__(self, meeting_topic, vote_number, yes)
        self.yes_voters = []
        self.no = no
        self.no_voters = []
        self.abstention = abstention
        self.abstention_voters = []
    

    # This function returns a string representation of the Vote object
    # Input: self - the Vote object
    # Output: a string representation of the Vote object
    def __repr__(self):
        return f"Vote({self.vote_number}, {self.yes}, {self.no}, {self.abstention})"

    # Function: to_dict
    # Description: Converts the object to a dictionary
    # Input:
    #   - self: the object to be converted
    #   - session_base_URI: the base URI for the session
    # Output:
    #   - A dictionary with the object's attributes
    
    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number, # The vote number
            'type': 'general', # The type of vote
            'yes': self.yes, # The number of 'yes' votes
            'no': self.no, # The number of 'no' votes
            'abstention': self.abstention, # The number of abstentions
            'passed': self.has_passed(), # Whether the vote has passed or not
            'voters': { # The voters for each option
                "yes": [f'{session_base_URI}members/{member.uuid}.json' for member in self.yes_voters], # The 'yes' voters
                "no": [f'{session_base_URI}members/{member.uuid}.json' for member in self.no_voters], # The 'no' voters
                "abstention": [f'{session_base_URI}members/{member.uuid}.json' for member in self.abstention_voters] # The abstaining voters
            }
        }

    # This function checks if the motion has passed by comparing the number of "yes" votes to the sum of "no" and "abstention" votes
    def has_passed(self):
        """
        Determines whether the motion has passed by comparing the number of "yes" votes to the sum of "no" and "abstention" votes.
    
        Returns:
            bool: True if the motion has passed, False otherwise.
        """
        # FIXME: This function does not check for quorum (rule 42.5 of parliament).
        # Quorum is the minimum number of members required to be present in order to conduct a vote.
        # Without quorum, the vote is not valid.
        return self.yes > self.no + self.abstention

    @staticmethod
    def from_table(meeting_topic, vote_number: int, vote_rows: NavigableString):
        """Generate a new Vote from a parsed table.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

        Returns:
            Vote: 
        """
        yes_str = clean_string(vote_rows[1].find_all(
            'td')[1].find('p').get_text())
        if not yes_str:
            # Sometimes, tables are empty... example: https://www.dekamer.be/doc/PCRI/html/55/ip100x.html
            return None
        yes = int(yes_str)
        no = int(clean_string(vote_rows[2].find_all(
            'td')[1].find('p').get_text()))
        abstention = int(clean_string(
            vote_rows[3].find_all('td')[1].find('p').get_text()))

        return GenericVote(meeting_topic, vote_number, yes, no, abstention)

    # This function sets the members who voted for a choice
    # and updates the count of yes voters.
    
    def set_yes_voters(self, l):
        """
        Set the members who voted for a choice.
    
        Args:
            l (List[Member]): A list of Members who voted for the choice.
        """
        # Check if there is a significant difference between the number of yes voters and the provided list.
        if abs(len(l) - self.yes) > 2:
            # If there is a difference, allow some tolerance and print a note.
            print(f'NOTE: The number of yes voters did not match the provided list: {len(l)} instead of {self.yes}')
            self.unsure = True
        # Update the count of yes voters and the list of yes voters.
        self.yes = len(l)
        self.yes_voters = l
        # Call a function to record post-vote activity.
        post_vote_activity(self, Choice.YES, l)

    def set_no_voters(self, l):
        """
        Sets the members who voted against.
    
        Args:
            l (List[Member]): A list of Members who voted against.
    
        Returns:
            None.
    
        Notes:
            If the number of no voters does not match the provided list, a NOTE is printed and the unsure attribute is set to True.
            The tolerance for inconsistencies is set to 2.
    
        """
        if abs(len(l) - self.no) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(
                f'NOTE: The number of no voters did not match the provided list: {len(l)} instead of {self.no}')
            self.unsure = True
        self.no = len(l)
        self.no_voters = l
        post_vote_activity(self, Choice.NO, l)

    # Function: set_abstention_voters
    # Description: Sets the members who abstained from voting for this motion
    # Args:
    #   - l (List[Member]): A list of Members who abstained from the vote
    # Returns: None
    
    def set_abstention_voters(self, l):
        """
        Sets the members who abstained from voting for this motion
    
        Args:
            l (List[Member]): A list of Members who abstained from the vote
        """
    
        # Check for inconsistencies in the counts and the reported names
        # Allow some tolerance for this
        if abs(len(l) - self.abstention) > 2:
            print(f'NOTE: The number of abstention voters did not match the provided list: {len(l)} instead of {self.abstention}')
            self.unsure = True
    
        # Set the number of abstentions and the abstention voters
        self.abstention = len(l)
        self.abstention_voters = l
    
        # Call the post_vote_activity function with the Choice.ABSTENTION and the abstention voters list
        post_vote_activity(self, Choice.ABSTENTION, l)


class LanguageGroupVote(GenericVote):
    """For some voting matters a majority in both Language Groups is needed"""

    # This function initializes a vote object with the given parameters
    # It takes a meeting topic, vote number, and votes from both the Dutch-speaking and French-speaking parts of Parliament
    # The vote counts are then added up and used to initialize a GenericVote object
    # The vote_NL and vote_FR attributes are also set to the given votes
    
    def __init__(self, meeting_topic, vote_number: int, vote_NL: Vote, vote_FR: Vote):
        """
        Initializes a vote object with the given parameters
    
        Args:
            meeting_topic (MeetingTopic): The meeting topic
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_NL (Vote): The Vote in the Dutch-speaking part of the Parliament
            vote_FR (Vote): The Vote in the French-speaking part of the Parliament
        """
        GenericVote.__init__(self, meeting_topic, vote_number, vote_NL.yes + vote_FR.yes,
                             vote_NL.no + vote_FR.no, vote_NL.abstention + vote_FR.abstention)
        self.vote_NL = vote_NL
        self.vote_FR = vote_FR

    # This function returns a string representation of a LanguageGroupVote object
    # It takes no arguments
    # It returns a string
    
    def __repr__(self):
        return "LanguageGroupVote(%d, %d, %d)" % (self.vote_number, self.vote_NL, self.vote_FR)

    # Function to_dict
    # Converts the Vote object to a dictionary
    
    # Parameters:
    # - self: the Vote object
    # - session_base_URI: the base URI for the session
    
    # Returns:
    # - A dictionary representing the Vote object
    
    def to_dict(self, session_base_URI: str):
        # Create a dictionary with the following keys:
        # - id: the vote number
        # - type: the type of vote (language_group)
        # - yes: the number of yes votes
        # - no: the number of no votes
        # - abstention: the number of abstention votes
        # - passed: whether the vote has passed or not
        # - voters: a dictionary with three keys (yes, no, abstention), each containing a list of member URIs
        # - detail: a dictionary with two keys (NL, FR), each containing a dictionary representing the VoteLanguage object
        
        return {
            'id': self.vote_number,
            'type': 'language_group',
            'yes': self.vote_NL.yes + self.vote_FR.yes,
            'no': self.vote_NL.no + self.vote_FR.no,
            'abstention': self.vote_NL.abstention + self.vote_FR.abstention,
            'passed': self.has_passed(),
            'voters': {
                "yes": [f'{session_base_URI}members/{member.uuid}.json' for member in self.yes_voters],
                "no": [f'{session_base_URI}members/{member.uuid}.json' for member in self.no_voters],
                "abstention": [f'{session_base_URI}members/{member.uuid}.json' for member in self.abstention_voters]
            },
            'detail': {
                "NL": self.vote_NL.to_dict(session_base_URI),
                "FR": self.vote_FR.to_dict(session_base_URI)
            }
        }

    # This function checks if the vote has passed in both halves of the parliament.
    # It returns a boolean value indicating whether the necessary majority has been obtained.
    
    def has_passed(self):
        """
        The vote has to pass in both halves of the parliament.
        
        Returns:
            bool: Has the vote obtained the necessary majority?
        """
        return self.vote_NL.has_passed() and self.vote_FR.has_passed()

    @staticmethod
    def from_table(meeting_topic, vote_number: int, vote_rows: NavigableString):
        """Generate a new Vote from a parsed table.

        Args:
            meeting_topic (MeetingTopic): The meeting topic
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

        Returns:
            Vote: 
        """
        yes_fr_text = clean_string(vote_rows[2].find_all('td')[1].find('p').get_text())
        no_fr_text = clean_string(vote_rows[3].find_all('td')[1].find('p').get_text())
        abstention_fr_text = clean_string(vote_rows[4].find_all('td')[1].find('p').get_text())

        yes_nl_text = clean_string(vote_rows[2].find_all('td')[3].find('p').get_text())
        no_nl_text = clean_string(vote_rows[3].find_all('td')[3].find('p').get_text())
        abstention_nl_text = clean_string(vote_rows[4].find_all('td')[3].find('p').get_text())

        if is_string_banned_or_empty(yes_fr_text) or is_string_banned_or_empty(no_fr_text) or is_string_banned_or_empty(abstention_fr_text) or is_string_banned_or_empty(yes_nl_text) or is_string_banned_or_empty(no_nl_text) or is_string_banned_or_empty(abstention_nl_text):
            print('Warning: invalid language group vote table found')
            return

        yes_fr = int(yes_fr_text)
        no_fr = int(no_fr_text)
        abstention_fr = int(abstention_fr_text)

        yes_nl = int(yes_nl_text)
        no_nl = int(no_nl_text)
        abstention_nl = int(abstention_nl_text)

        return LanguageGroupVote(meeting_topic, vote_number, GenericVote(meeting_topic, vote_number, yes_nl, no_nl, abstention_nl), GenericVote(meeting_topic, vote_number, yes_fr, no_fr, abstention_fr))


class ElectronicGenericVote(Vote):
    """Some voting are anonymously organised electronically. We don't have the names in this case"""

    """
    The __init__ method initializes a Vote object with the given meeting topic, vote number, and vote counts.
    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        yes (int): Number of yes votes
        no (int): Number of no votes
    """
    def __init__(self, meeting_topic, vote_number: int, yes: int, no: int):
        Vote.__init__(self, meeting_topic, vote_number, yes)
        self.no = no

    # This function returns a string representation of an ElectronicGenericVote object
    # It includes the vote number, number of yes votes, and number of no votes
    # Parameters:
    # - self: an instance of ElectronicGenericVote class
    # Returns:
    # - a string representation of the object
    def __repr__(self):
        return f"ElectronicGenericVote({self.vote_number}, {self.yes}, {self.no})"

    # Determines if the student has passed based on the number of "yes" and "no" answers.
    
    def has_passed(self):
        """
        Returns True if the student has passed, False otherwise.
        A student passes if they have answered more "yes" than "no" and the total number of answers is greater than 75.
        """
        return self.yes > self.no and self.yes + self.no > 75

    # This function converts the current object into a dictionary
    # Parameters:
    # - session_base_URI: a string representing the base URI of the current session
    # Returns:
    # - a dictionary containing the object's properties
    
    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number, # represents the unique identifier of the vote
            'type': 'electronic_generic', # represents the type of the vote
            'yes': self.yes, # represents the number of 'yes' votes
            'no': self.no, # represents the number of 'no' votes
            'passed': self.has_passed() # represents whether the vote has passed or not
        }


class ElectronicAdvisoryVote(Vote):
    """Some voting are anonymously organised electronically to inquire whether more opinions are required.
    We don't have the names in this case
    """

    """
    Initializes a Vote object with the provided meeting topic, vote number, and number of yes votes.
    Args:
        meeting_topic (MeetingTopic): The topic of the meeting.
        vote_number (int): The number of the vote in the meeting.
        yes (int): The number of yes votes.
    """ 
    def __init__(self, meeting_topic, vote_number: int, yes: int):
        Vote.__init__(self, meeting_topic, vote_number, yes)

    # This method returns a string representation of the ElectronicAdvisoryVote object.
    # It includes the vote number and whether the vote was a "yes" or "no".
    
    def __repr__(self):
        """
        Returns a string representation of the ElectronicAdvisoryVote object.
        
        Args:
        - self: the ElectronicAdvisoryVote object
        
        Returns:
        - A string representation of the ElectronicAdvisoryVote object, including the vote number and whether the vote was a "yes" or "no".
        """
        return f"ElectronicAdvisoryVote({self.vote_number}, {self.yes})"

    # This function checks if an advisory request has passed by comparing the number of yes votes to a threshold.
    # If the number of yes votes is greater than 50% of the total votes, the function returns True, indicating that the motion has passed.
    # Otherwise, the function returns False, indicating that the motion has not passed.
    
    def has_passed(self):
        """Checks if an advisory request has passed.
        
        Compares the number of yes votes to a threshold of 50% of the total votes.
        
        Returns:
            bool: True if the motion has passed, False otherwise.
        """
        return self.yes > 50

    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number,
            'type': 'electronic_advisory',
            'yes': self.yes,
            'passed': self.has_passed()
        }
    


# This function generates a new electronic vote from a parsed table
# It takes in the meeting topic, vote number, and vote start node as arguments
# It returns a Vote object

def electronic_vote_from_table(meeting_topic, vote_number: int, vote_start_node: NavigableString):
    """
    Generate a new electronic (advisory or generic) vote from a parsed table.

    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        vote_start_node (NavigableString): Vote start node as obtained by BeautifulSoup

    Returns:
        Vote: A Vote object
    """

    # Get the number of "yes" votes
    yes = int(clean_string(vote_start_node.find_all('td')[1].find('p').get_text()))

    # Find the next sibling of the vote start node
    vote_end_node = vote_start_node.find_next_sibling().find_next_sibling()

    # If there is no next sibling or it is not a table, return an ElectronicAdvisoryVote object
    if not vote_end_node or vote_end_node.name != 'table':
        return ElectronicAdvisoryVote(meeting_topic, vote_number, yes)

    # Get the number of "no" votes
    no = int(clean_string(vote_end_node.find_all('td')[1].find('p').get_text()))

    # Return an ElectronicGenericVote object
    return ElectronicGenericVote(meeting_topic, vote_number, yes, no)


"""
This function posts a vote activity for each member in the given list.

@param vote: A Vote object representing the vote being cast.
@param choice: A Choice object representing the option being voted for.
@param members: A list of Member objects representing the members who are casting their votes.

@return: None
"""

def post_vote_activity(vote: Vote, choice: Choice, members: List):
    for member in members:
        member.post_activity(activity.VoteActivity(member, vote, choice))
