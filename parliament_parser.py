import json
import requests
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from member import Member
from meeting import Meeting
import json
from os import path, makedirs
import functools
from util import normalize_str


# This function takes in three parameters: a base path, a base URI, and a member object.
# It returns the result of calling the dump_json method on the member object with the base path and base URI as arguments.
def member_to_URI(base_path, base_URI, member):
    return member.dump_json(base_path, base_URI)


# This function takes in three parameters: base_path, base_URI, and meeting
# base_path: the base path of the meeting
# base_URI: the base URI of the meeting
# meeting: the meeting object that will be converted to JSON format

def meeting_to_URI(base_path, base_URI, meeting):
    # The dump_json method is called on the meeting object to convert it to JSON format
    # The base_path and base_URI are passed as arguments to the dump_json method
    # The JSON representation of the meeting object is returned
    return meeting.dump_json(base_path, base_URI)


class ParliamentarySession:
    '''
    A ParliamentarySession object is the main entryway to the scraper.
    It is constructed based on the Session one wants to obtain information on.
    From there information can be obtained on the members of the parliament in that session and its meetings.
    '''
    sessions = {
        55: {'from': '2019-06-20', 'to': '2024-06-19'},
        54: {'from': '2014-06-19', 'to': '2019-04-25'},
        53: {'from': '2010-06-13', 'to': '2014-04-24'},
        52: {'from': '2007-06-10', 'to': '2010-05-06'},
    }

    # Function: dump_json
    # Description: Generates JSON files for a session and its related documents, questions, and meetings.
    # Input:
    #   - self: The current instance of the class.
    #   - output_path: The path where the JSON files will be saved.
    #   - base_URI: The base URI for the session.
    # Output:
    #   - Returns the URI for the session JSON file.
    
    def dump_json(self, output_path: str, base_URI="/"):
        # Importing the concurrent.futures module for multi-threading.
        import concurrent.futures
        
        # Retrieving the members and plenary meetings for the session.
        self.get_members()
        self.get_plenary_meetings()
        
        # Creating the base path for the session.
        base_path = path.join(output_path, "sessions", f'{self.session}')
        
        # Updating the base URI for the session.
        base_URI = f'{base_URI}sessions/{self.session}/'
        
        # Creating the directory structure for the session.
        makedirs(base_path, exist_ok=True)
        
        # Limiting the workers helps with reducing the lock contention.
        # With more workers there is little to gain.
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            
            # Generating the URIs for the plenary meetings.
            meeting_URIs = list(executor.map(functools.partial(
                meeting_to_URI, base_path, base_URI), self.plenary_meetings))
            
            # Generating the URIs for the members.
            members_URIs = list(executor.map(functools.partial(
                member_to_URI, base_path, base_URI), self.members))
        
        # Creating the directory structure for the legislation and questions.
        makedirs(path.join(base_path, "legislation"), exist_ok=True)
        makedirs(path.join(base_path, "questions"), exist_ok=True)
        
        # Generating the JSON files for the questions.
        for question in self.questions.values():
            question.json(base_path, base_URI)
        
        # Generating the JSON files for the documents.
        for document in self.documents.values():
            document.json(base_path, base_URI)
        
        # Generating the unfolded JSON file for the legislation.
        with open(path.join(base_path, 'legislation', 'unfolded.json'), 'w') as fp:
            json.dump(
                {
                    document.document_number: document.json_representation(base_URI)
                    for document in self.documents.values()
                },
                fp
            )
        
        # Generating the unfolded JSON file for the questions.
        with open(path.join(base_path, 'questions', 'unfolded.json'), 'w') as fp:
            json.dump(
                {
                    document.document_number: document.json_representation(base_URI)
                    for document in self.questions.values()
                },
                fp
            )
        
        # Generating the index JSON file for the legislation.
        with open(path.join(base_path, 'legislation', 'index.json'), 'w') as fp:
            json.dump({document.document_number: f'{base_URI}{document.uri()}' for document in self.documents.values()}, fp)
        
        # Generating the index JSON file for the questions.
        with open(path.join(base_path, 'questions', 'index.json'), 'w') as fp:
            json.dump({question.document_number: f'{base_URI}{question.uri()}' for question in self.questions.values()}, fp)
        
        # Generating the JSON file for the session.
        with open(path.join(base_path, 'session.json'), 'w') as fp:
            json.dump({
                'id': self.session,
                'start': self.start,
                'end': self.end,
                'members': members_URIs,
                'legislation': f'{base_URI}legislation/index.json',
                'questions': f'{base_URI}questions/index.json',
                'meetings': {'plenary': meeting_URIs}}, fp)
        
        # Returning the URI for the session JSON file.
        return path.join(base_URI, 'session.json')

    # This function initializes a new instance of the scraper
    # It takes in a session integer as an argument
    # Only sessions 55 to 52 are supported for now
    def __init__(self, session: int):
        """
        Initialize a new instance of the scraper
        
        Args:
            session (int): Specify the session for which the scraper should be constructed
        
        Note:
            Only sessions 55 to 52 are supported for now.
        """
        
        # Check if the session is within the supported range
        assert (session < 56 and session > 51), 'Only sessions 52-55 are available via this API'
        
        # Set the session variable
        self.session = session
        
        # Initialize empty lists and dictionaries for data storage
        self.plenary_meetings = []
        self.members_dict = {}
        self.questions = {}
        self.documents = {}
        self.members = []
        
        # Set the start and end dates for the session
        self.start = ParliamentarySession.sessions[session]['from']
        self.end = ParliamentarySession.sessions[session]['to']
        
        # Initialize dictionaries for mapping member names to IDs
        self._members_fn_ln = {}
        self._members_ln_fn = {}
        
        # Initialize a requests session with retry strategy
        self._requests_session = requests.Session()
        retry_strategy = Retry(total=5, backoff_factor=1)
        self._requests_session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=retry_strategy))

    @property
    def requests_session(self):
        return self._requests_session

    # Documented code:
    
    def find_member(self, query: str):
        """
        This function finds a Member object related to the given query.
    
        Args:
            query (str): The name of the member in the format "{last_name} {first_name}" as listed in the meeting notes.
    
        Returns:
            Member: The related Member object if one is found.
        """
        # Check if the members list is empty and fetch the members if it is.
        if not self.members:
            self.get_members()
    
        # Normalize the query string.
        normalized = normalize_str(query)
    
        # Check if the normalized query string is in the dictionary of members indexed by first name and last name.
        if normalized in self._members_fn_ln:
            return self._members_fn_ln[normalized]
    
        # Iterate over the members list and check if any member has the given name.
        for member in self.members:
            if member.has_name(query):
                return member
    
        # If no member is found, print an error message.
        print(f'Undefined member: {query}')

    # This function returns a dictionary of members
    # Key: member name and party
    # Value: member object
    def get_members_dict(self):
        # If the dictionary is not already created, create an empty dictionary
        if not self.members_dict:
            self.members_dict = {}
            # Iterate through each member
            for member in self.members:
                # Normalize the first and last name of the member
                first_name = normalize_str(member.first_name).decode()
                last_name = normalize_str(member.last_name).decode()
                # Add the member to the dictionary with different variations of their name and party
                self.members_dict[f'{first_name}, {last_name}'] = member
                self.members_dict[f'{first_name}, {last_name} {member.party}'] = member
                self.members_dict[f'{first_name}, {last_name}, {member.party}'] = member
                self.members_dict[f'{first_name}, {last_name}'.replace('-', ' ')] = member
                # If the member belongs to the "Vooruit" party, add additional variations of their name and party
                if member.party == "Vooruit":
                    self.members_dict[f'{first_name}, {last_name}, sp.a'] = member
                    self.members_dict[f'{first_name}, {last_name} sp.a'] = member
        # Return the dictionary of members
        return self.members_dict

    # This function returns an overview of all Plenary meetings in the session.
    # It takes an optional boolean parameter 'refresh' which, when set to True, fully re-parses the scraped document.
    # If 'refresh' is False and 'self.plenary_meetings' is not empty, it returns the cached list of meetings.
    # Otherwise, it scrapes the URL and returns a list of Meeting objects.
    
    def get_plenary_meetings(self, refresh=False):
        """
        This API returns an overview of all Plenary meetings in the session.
        A list of Meeting objects is returned.
    
        Args:
            refresh (bool, optional): Should we fully reparse the scraped document? Defaults to False.
    
        Returns:
            list(Meeting): List of all known plenary meetings.
        """
        # If 'refresh' is True or 'self.plenary_meetings' is empty, we need to scrape the URL and parse the document.
        if refresh or not self.plenary_meetings:
            # Construct the URL for the current session.
            URL = 'https://www.dekamer.be/kvvcr/showpage.cfm?section=/cricra&language=nl&cfm=dcricra.cfm?type=plen&cricra=cri&count=all&legislat=%02d' % (
                self.session)
            # Send a GET request to the URL and get the response.
            page = self.requests_session.get(URL)
            # Parse the response using BeautifulSoup.
            soup = BeautifulSoup(page.content, 'lxml')
            # Find all 'tr' elements in the parsed document.
            meetings = soup.find_all('tr')
            # Initialize an empty list to store the Meeting objects.
            self.plenary_meetings = []
            # Loop through all the 'tr' elements and create a Meeting object for each of them.
            for meeting in meetings:
                self.plenary_meetings.append(Meeting.from_soup(meeting, self))
        # If 'refresh' is False and 'self.plenary_meetings' is not empty, we return the cached list of meetings.
        #self.plenary_meetings = self.plenary_meetings[:10]
        return self.plenary_meetings

    # Documented code
    
    def get_members(self):
        """
        Get all known parliament members within this session
    
        Returns:
            list(Member): list of all known members within the session
        """
        # Check if members have already been fetched
        if not self.members:
            # Open the JSON file containing the composition data for the session
            with open(f'data/composition/{self.session}.json') as json_file:
                # Load the data from the JSON file
                data = json.load(json_file)
                # Create Member objects from the data and add them to the list of members
                for entry in data:
                    member = Member.from_json(entry)
                    self.members.append(member)
                # Link the members to their replacements
                for member, entry in zip(self.members, data):
                    if 'replaces' in entry:
                        replaces = entry['replaces']
                        for replacement in replaces:
                            referenced_member = self.find_member(
                                replacement['name'])
                            del replacement['name']
                            replacement['member'] = referenced_member.uuid
                        member.set_replaces(replaces)
            # Create a dictionary mapping member names to Member objects
            self._members_fn_ln = {normalize_str(
                f'{member.last_name} {member.first_name}'): member for member in self.members}
        # Return the list of members
        return self.members
