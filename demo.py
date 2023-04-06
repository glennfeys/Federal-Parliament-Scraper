# This code uses the Parliament_parser library to retrieve information about parliamentary sessions
from parliament_parser import ParliamentarySession

# Create an object representing a parliamentary session
session = ParliamentarySession(55)

# Get an object containing all known members during the session
session.get_members()

# Get all plenary meetings
meetings = session.get_plenary_meetings()

# Loop through the topics of the first meeting in reverse order and print the title and vote information
topics = meetings[0].get_meeting_topics() # <- This is a dict mapping the agenda item number onto an object
for idx in reversed(list(topics.keys())):
    # Print the title of the topic
    print("%d. %s" % (idx, topics[idx].get_title()[0])) # <- Textual objects (titles and section names) are stored as tuples 
    # If there is a vote, print the results
    if topics[idx].get_votes():
        vote = topics[idx].get_votes()[0]
        print(vote)
        print("Ja: %s" % ([str(voter) for voter in vote.yes_voters]))
        print("Nee: %s" % ([str(voter) for voter in vote.no_voters]))
        print("Onthouding: %s" % ([str(voter) for voter in vote.abstention_voters]))

# Loop through all meetings and get their topics
for meeting in meetings:
    meeting.get_meeting_topics()