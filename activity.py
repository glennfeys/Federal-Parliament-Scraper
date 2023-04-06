# Documenting the code

from vote import Vote
from common import Choice


class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    on a given date.
    """

    def __init__(self, member, date):
        """
        Initializes an Activity object.

        Args:
        - member: a member of Parliament
        - date: the date of the activity
        """
        self.member = member
        self.date = date

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the Activity object.

        Args:
        - base_URI: the base URI for the object

        Returns:
        - a dictionary with the type of activity and its details
        """
        raise NotImplementedError()


class VoteActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    action is the casting of a name vote.
    """

    def __init__(self, member, vote: Vote, choice: Choice):
        """
        Initializes a VoteActivity object.

        Args:
        - member: a member of Parliament
        - vote: a Vote object
        - choice: the choice made by the member in the vote
        """
        Activity.__init__(self, member, vote.meeting.date)
        self.vote = vote
        self.choice = choice

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the VoteActivity object.

        Args:
        - base_URI: the base URI for the object

        Returns:
        - a dictionary with the type of activity, the topic of the vote and the choice made by the member
        """
        return {
            "type": "vote",
            "topic": f'{base_URI}{self.vote.meeting_topic.get_uri()}',
            "choice": str(self.choice)
        }


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
        Initializes a TopicActivity object.

        Args:
        - member: a member of Parliament
        - meeting: a Meeting object
        - meeting_topic: a MeetingTopic object
        """
        Activity.__init__(self, member, meeting.date)
        self.meeting_topic = meeting_topic

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the TopicActivity object.

        Args:
        - base_URI: the base URI for the object

        Returns:
        - a dictionary with the type of activity and the topic of the meeting
        """
        return {
            "type": "topic",
            "topic": f'{base_URI}{self.meeting_topic.get_uri()}'
        }


class QuestionActivity(Activity):
    """
    A QuestionActivity represents the fact that the member
    has asked a question (orally or written).
    """

    def __init__(self, member, date, question):
        """
        Initializes a QuestionActivity object.

        Args:
        - member: a member of Parliament
        - date: the date of the question
        - question: a Question object
        """
        Activity.__init__(self, member, date)
        self.question = question

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the QuestionActivity object.

        Args:
        - base_URI: the base URI for the object

        Returns:
        - a dictionary with the type of activity and the URI of the question
        """
        return {
            "type": "question",
            "question": f'{base_URI}{self.question.uri()}'
        }


class LegislativeActivity(Activity):
    """
    A LegislativeActivity represents the fact that the member
    has been the author of a Bill or Bill Proposal.
    """

    def __init__(self, member, date, document):
        """
        Initializes a LegislativeActivity object.

        Args:
        - member: a member of Parliament
        - date: the date of the legislative activity
        - document: a Document object
        """
        Activity.__init__(self, member, date)
        self.document = document

    def dict(self, base_URI):
        """
        Returns a dictionary representation of the LegislativeActivity object.

        Args:
        - base_URI: the base URI for the object

        Returns:
        - a dictionary with the type of activity and the URI of the document
        """
        return {
            "type": "legislation",
            "document": f'{base_URI}{self.document.uri()}'
        }