from bs4 import BeautifulSoup
import parliament_parser
import requests
import dateparser
from activity import LegislativeActivity, QuestionActivity
import re
import json
from util import normalize_str
from os import path


def extract_name(name: str):
    match = re.match(r"(.+, .+) (\S+)$", name)
    if match and match.group(1):
        res = match.group(1)
        res = res.replace(' CD&V -', '') # Fixes a bug caused by "het kartel"
        if res[-1] == ',':
            res = res[:-1]
        return res
    else:
        return name



class ParliamentaryDocument:
    # Initializes the Document object with session and document number
    # and sets initial values for descriptor, keywords, title, document type, date, and authors
    def __init__(self, session, document_number):
        self.session = session
        self.document_number = document_number
        self.descriptor = None  # The descriptor of the document
        self.keywords = None  # The keywords associated with the document
        self.title = None  # The title of the document
        self.document_type = None  # The type of the document
        self.date = dateparser.parse(session.start)  # The date the document was created
        self.authors = []  # The authors of the document
        self._initialize()  # Initializes the Document object
        self.session.documents[document_number] = self  # Adds the document to the session's documents dictionary
        self._register_activities()  # Registers the document's activities

    # This function returns the URI for a legislative document on the Belgian parliament website.
    # The URI includes the legislative session and document number.
    # Example: https://www.dekamer.be/kvvcr/showpage.cfm?section=/flwb&language=nl&cfm=/site/wwwcfm/flwb/flwbn.cfm?lang=N&legislat=55&dossierID=1234
    
    def description_uri(self):
        return f'https://www.dekamer.be/kvvcr/showpage.cfm?section=/flwb&language=nl&cfm=/site/wwwcfm/flwb/flwbn.cfm?lang=N&legislat={self.session.session}&dossierID={self.document_number}'

    # This function returns the URI of a legislation document in JSON format
    # It takes no arguments
    # It uses the document number property of the current object to construct the URI
    
    def uri(self):
        """
        Returns the URI of a legislation document in JSON format
        :return: string
        """
        return f'legislation/{self.document_number}.json'

    # Function: json_representation
    # Description: Returns a JSON representation of the document
    # Input: self - the document object
    #        base_URI - the base URI for the document
    # Output: A dictionary representing the JSON representation of the document
    def json_representation(self, base_URI="/"):
        # Initialize an empty dictionary to store the JSON representation
        result = {}
        
        # Add the document number to the dictionary
        result['document_number'] = self.document_number
        
        # If the document type exists, add it to the dictionary
        if self.document_type:
            result['document_type'] = self.document_type
        
        # If the title exists, add it to the dictionary
        if self.title:
            result['title'] = self.title
        
        # Add the source of the document to the dictionary
        result['source'] = self.description_uri()
        
        # If the date does not exist, parse the session start date and add it to the dictionary
        if not self.date:
            self.date = dateparser.parse(self.session.start)
        result['date'] = self.date.isoformat()
        
        # Add the authors to the dictionary, with their URIs appended to the base URI
        result['authors'] = [
            f'{base_URI}{author.uri()}' for author in self.authors]
        
        # If the descriptor exists, add it to the dictionary
        if self.descriptor:
            result['descriptor'] = self.descriptor
        
        # If the keywords exist, add them to the dictionary
        if self.keywords:
            result['keywords'] = self.keywords
        
        # Return the JSON representation dictionary
        return result

    # This function creates a JSON file for a legislation document and returns the URI of the document.
    # Parameters:
    # - self: the current object instance
    # - base_path: the base directory path where the JSON file will be saved
    # - base_URI: the base URI of the document (default: "/")
    # Returns:
    # - The URI of the document
    def json(self, base_path, base_URI="/"):
        # Append "legislation" to the base path
        base_path = path.join(base_path, "legislation")
        # Open the JSON file for writing
        with open(path.join(base_path, f'{self.document_number}.json'), 'w+') as fp:
            # Write the JSON representation of the legislation document to the file
            json.dump(self.json_representation(base_URI), fp, ensure_ascii=False)
        # Return the URI of the document
        return f'{base_URI}{self.uri}'

    # Initializes the object with the given retry count.
    # Parameters:
    #   - retry: the number of times to retry initialization in case of errors.
    def _initialize(self, retry=0):
        # Sends a GET request to the description URI and parses the response using BeautifulSoup.
        page = self.session.requests_session.get(self.description_uri())
        soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
        
        # Finds the 'Story' div element on the page.
        content = soup.find('div', {'id': 'Story'})
        
        # If the 'Story' div is not found or contains the text 'not found', returns.
        if not content or "not found" in content.get_text():
            return
        
        # If the 'Story' div contains the text 'Er heeft zich een fout voorgedaan', retries initialization up to 10 times.
        if "Er heeft zich een fout voorgedaan" in content.get_text():
            if retry >= 10:
                print('Gave up on', self.description_uri())
                return
            else:
                self._initialize(retry=retry + 1)
                return
        
        # Finds the 'Indieningsdatum' or a date in the format '[0-9]+/[0-9]+/[0-9]+' on the page and parses it using dateparser.
        proposal_date = soup.find('td', text=re.compile('Indieningsdatum'))
        if not proposal_date:
            proposal_date = soup.find('td', text=re.compile('[0-9]+/[0-9]+/[0-9]+'))
            if proposal_date:
                self.date = dateparser.parse(proposal_date.get_text(), languages=['nl'])
        else:
            self.date = dateparser.parse(
                proposal_date.parent.find_all('td')[-1].get_text(), languages=['nl'])
        
        # Finds the 'Eurovoc-hoofddescriptor' on the page and sets it as the descriptor of the object.
        descriptor = soup.find(
            'td', text=re.compile('Eurovoc-hoofddescriptor'))
        if descriptor:
            self.descriptor = descriptor.parent.find_all('td')[-1].get_text().split(' | ')
        
        # Finds the 'Eurovoc descriptoren' on the page and sets them as the keywords of the object.
        keywords = soup.find('td', text=re.compile('Eurovoc descriptoren'))
        if keywords:
            self.keywords = keywords.parent.find_all(
                'td')[-1].get_text().split(' | ')
        
        # Finds the title of the page and sets it as the title of the object.
        title = content.find('h4')
        if title:
            self.title = title.get_text().strip()
        
        # Finds the 'Document type' on the page and sets it as the document type of the object.
        doc_type_row = [tag for tag in soup.find_all(
            'td', {'class': "td1x"}) if 'Document type' in tag.get_text()]
        self.document_type = doc_type_row[0].parent.find(
            'td', {'class': 'td0x'}).find_all(text=True)[0][3:]
        
        # Finds the 'Auteur(s)' on the page and sets the authors of the object.
        authors = [tag for tag in soup.find_all(
            'td', {'class': "td1x"}) if 'Auteur(s)' in tag.get_text()]
        if authors:
            authors = authors[0].parent.find(
                'td', {'class': 'td0x'}).find_all(text=True)
            authors = [text.strip() for text in authors if (
                not str(text).isspace()) and ', ' in text]
            for name in authors:
                name = normalize_str(name).decode()
                if name in self.session.get_members_dict():
                    self.authors.append(self.session.get_members_dict()[name])
                elif extract_name(name) in self.session.get_members_dict():
                    self.authors.append(self.session.get_members_dict()[
                                        extract_name(name)])
                else:
                    print("D:" + name)

    # This function registers the legislative activities of authors.
    # If there are no authors, the function returns.
    # For each author, a LegislativeActivity object is created and added to their activity list.
    
    def _register_activities(self):
        """
        Registers the legislative activities of authors.
    
        If there are no authors, the function returns.
    
        For each author, a LegislativeActivity object is created and added to their activity list.
    
        :return: None
        """
        if not self.authors:
            return
        for author in self.authors:
            author.post_activity(LegislativeActivity(author, self.date, self))


class ParliamentaryQuestion:
    # Initializes a new instance of the Question class.
    # Parameters:
    # - session: The session associated with the question.
    # - document_number: The document number of the question.
    def __init__(self, session, document_number: str):
        from datetime import datetime
        
        # Initializes the session and document number properties.
        self.session = session
        self.document_number = document_number
        
        # Initializes the authors, title, and responding minister properties.
        self.authors = []
        self.title = None
        self.responding_minister = None
        
        # Parses the session start date and initializes the date property.
        self.date = dateparser.parse(session.start)
        
        # Calls the _initialize method to perform additional initialization.
        self._initialize()
        
        # Adds the question to the session's questions dictionary.
        self.session.questions[document_number] = self
        
        # Calls the _register_activities method to register activities related to the question.
        self._register_activities()

    # This function registers activities for authors who have posted questions
    # Input: None
    # Output: None
    
    def _register_activities(self):
        """
        This function registers activities for authors who have posted questions.
        If there are no authors, the function returns None.
        """
        if not self.authors:
            return
        for author in self.authors:
            author.post_activity(QuestionActivity(author, self.date, self))
            """
            For each author, the function calls the post_activity method of the author object.
            The post_activity method takes three arguments: the author object, the date of the question, and the question object itself.
            This registers a QuestionActivity for the author.
            """
    

    # This function returns the URI of a document in JSON format
    # It takes no input parameters
    # It returns a string containing the URI of the document
    
    def uri(self):
        return f'questions/{self.document_number}.json'

    # This function returns a JSON representation of a document object
    # Parameters:
    # - self: the document object
    # - base_URI (optional): the base URI to use for author URIs
    
    def json_representation(self, base_URI="/"):
        # Create an empty dictionary to hold the JSON representation
        result = {}
        
        # Add the document number and title to the dictionary
        result['document_number'] = self.document_number
        result['title'] = self.title
        
        # If the document date is not set, parse it from the session start time
        if not self.date:
            self.date = dateparser.parse(self.session.start)
        result['date'] = self.date.isoformat()
        
        # Add the source URI to the dictionary
        result['source'] = self.description_uri()
        
        # If there is a responding minister, add their name and department to the dictionary
        if self.responding_minister:
            result['responding_minister'] = self.responding_minister
            result['responding_department'] = self.responding_department
        
        # Add the URIs of all authors to the dictionary
        result['authors'] = [
            f'{base_URI}{author.uri()}' for author in self.authors]
        
        # Return the completed JSON representation
        return result

    # This function takes in a base path and a base URI as input and generates a JSON file with the given document number
    # The JSON file is saved in the "questions" directory within the base path
    # The function returns the URI of the generated JSON file
    
    def json(self, base_path, base_URI="/"):
        # Append "questions" to the base path
        base_path = path.join(base_path, "questions")
        
        # Open a new file with the document number as the filename and write the JSON representation of the object to it
        with open(path.join(base_path, f'{self.document_number}.json'), 'w+') as fp:
            json.dump(self.json_representation(base_URI), fp, ensure_ascii=False)
        
        # Return the URI of the generated JSON file
        return f'{base_URI}{self.uri}'

    # This function returns the URI for a specific legislative document on the Belgian Chamber of Representatives website.
    # The URI is constructed using the session and document number of the document.
    # The returned URI will allow the user to view the document on the website.
    def description_uri(self):
        return f'https://www.dekamer.be/kvvcr/showpage.cfm?section=inqo&language=nl&cfm=inqoXml.cfm?db=INQO&legislat={self.session.session}&dossierID=Q{self.document_number}'

    # Initializes the object with the given retry count
    # and retrieves the page content from the description URI.
    # Then, it parses the content using BeautifulSoup and retrieves the body.
    # If the body is empty or contains "does not exist", it returns.
    # If the body contains "Er heeft zich een fout voorgedaan", it retries up to 10 times.
    # It then retrieves the authors from the page content and normalizes their names.
    # If a name matches a member in the session's members dictionary, it adds the member to the authors list.
    # If not, it prints the name.
    # It then retrieves the responding minister and department, if they exist.
    # Finally, it retrieves the title and date of the page content.
    
    def _initialize(self, retry=0):
        # Retrieve page content from description URI
        page = self.session.requests_session.get(self.description_uri())
        # Parse content using BeautifulSoup
        soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
        # Retrieve body
        body = soup.find('body')
        # If body is empty or contains "does not exist", return
        if not body or "does not exist" in body.get_text():
            return
        # If body contains "Er heeft zich een fout voorgedaan", retry up to 10 times
        if "Er heeft zich een fout voorgedaan" in body.get_text():
            if retry >= 10:
                print('Gave up on', self.description_uri())
                return
            else:
                self._initialize(retry=retry + 1)
                return
        # Retrieve authors from page content and normalize their names
        authors = [tag for tag in soup.find_all(
            'td') if 'Auteur(s)' in tag.get_text()]
        if authors:
            authors = authors[0].parent.find_all(
                'td')[1].get_text().split('\n')
            authors = [','.join(text.strip().split(
                ',')[:-1]) for text in authors if (not str(text).isspace()) and ', ' in text]
        for name in authors:
            name = normalize_str(name).decode()
            # If name matches a member in session's members dictionary, add member to authors list
            if name in self.session.get_members_dict():
                self.authors.append(self.session.get_members_dict()[name])
            elif extract_name(name) in self.session.get_members_dict():
                self.authors.append(self.session.get_members_dict()[
                                    extract_name(name)])
            else:
                # If name doesn't match any member, print name
                print("Q:" + name)
        # Retrieve responding minister and department, if they exist
        responding_minister_cell = soup.find(
            'i', text=re.compile('Antwoordende minister'))
        if responding_minister_cell:
            self.responding_minister = responding_minister_cell.find_parent('tr').find_all('td')[
                1].get_text().strip()[:-1]
            self.responding_department = responding_minister_cell.find_parent('tr').find_next('tr').get_text().strip()
        # Retrieve title and date of page content
        title = soup.find('i', text=re.compile('Titel'))
        if title:
            self.title = title.find_parent('tr').find_all('td')[
                1].get_text().strip()
            self.title = "\n".join(item.strip()
                                   for item in self.title.split('\n') if item.strip())
        date = soup.find('i', text=re.compile('Datum bespreking'))
        if date:
            self.date = dateparser.parse(
                date.find_parent('tr').find_all('td')[1].get_text().strip(), languages=['nl'])
