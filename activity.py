# Documenting the code

# Importing the necessary modules
from vote import Vote
from common import Choice

# Defining the Activity class
class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    on a given date.
    """

    def __init__(self, member, date):
        """
        Initializes the Activity object with the given member and date.

        :param member: The member of Parliament.
        :param date: The date of the activity.
        """
        self.member = member
        self.date = date

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the Activity object.

        :param base_URI: The base URI of the object.
        :return: A dictionary representing the Activity object.
        """
        raise NotImplementedError()


# Defining the VoteActivity class
class VoteActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    action is the casting of a name vote.
    """

    def __init__(self, member, vote: Vote, choice: Choice):
        """
        Initializes the VoteActivity object with the given member, vote, and choice.

        :param member: The member of Parliament.
        :param vote: The vote object.
        :param choice: The choice made by the member.
        """
        Activity.__init__(self, member, vote.meeting.date)
        self.vote = vote
        self.choice = choice

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the VoteActivity object.

        :param base_URI: The base URI of the object.
        :return: A dictionary representing the VoteActivity object.
        """
        return {
            "type": "vote",
            "topic": f'{base_URI}{self.vote.meeting_topic.get_uri()}',
            "choice": str(self.choice)
        }


# Defining the TopicActivity class
class TopicActivity(Activity):
    """
    A TopicActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    this means their name has appeared in a topic in
    the meeting. The section in which this topic appeared
    is recorded as well as the specific meeting.
    """

    def __init__(self, member, meeting, meeting_topic):
        """
        Initializes the TopicActivity object with the given member, meeting, and meeting_topic.

        :param member: The member of Parliament.
        :param meeting: The meeting object.
        :param meeting_topic: The topic discussed in the meeting.
        """
        Activity.__init__(self, member, meeting.date)
        self.meeting_topic = meeting_topic

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the TopicActivity object.

        :param base_URI: The base URI of the object.
        :return: A dictionary representing the TopicActivity object.
        """
        return {
            "type": "topic",
            "topic": f'{base_URI}{self.meeting_topic.get_uri()}'
        }


# Defining the QuestionActivity class
class QuestionActivity(Activity):
    """
    A QuestionActivity represents the fact that the member
    has asked a question (orally or written).
    """

    def __init__(self, member, date, question):
        """
        Initializes the QuestionActivity object with the given member, date, and question.

        :param member: The member of Parliament.
        :param date: The date of the question.
        :param question: The question asked by the member.
        """
        Activity.__init__(self, member, date)
        self.question = question

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the QuestionActivity object.

        :param base_URI: The base URI of the object.
        :return: A dictionary representing the QuestionActivity object.
        """
        return {
            "type": "question",
            "question": f'{base_URI}{self.question.uri()}'
        }


# Defining the LegislativeActivity class
class LegislativeActivity(Activity):
    """
    A LegislativeActivity represents the fact that the member
    has been the author of a Bill or Bill Proposal.
    """

    def __init__(self, member, date, document):
        """
        Initializes the LegislativeActivity object with the given member, date, and document.

        :param member: The member of Parliament.
        :param date: The date of the legislative activity.
        :param document: The document related to the legislative activity.
        """
        Activity.__init__(self, member, date)
        self.document = document

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the LegislativeActivity object.

        :param base_URI: The base URI of the object.
        :return: A dictionary representing the LegislativeActivity object.
        """
        return {
            "type": "legislation",
            "document": f'{base_URI}{self.document.uri()}'
        }