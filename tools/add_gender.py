# This script retrieves information from Wikidata and Wikipedia to enrich a dataset of members
# It takes as input a JSON file containing information about the members
# It outputs a new JSON file with additional information about each member, including their gender

import json
import requests
import pywikibot
import tqdm

# Set up Pywikibot to use the Wikidata site
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

def main():
    # Open the input JSON file
    with open('data/composition/52.json', 'r') as fp:
        # Load the members data from the JSON file
        members = json.load(fp)
        # Iterate over each member
        for member in tqdm.tqdm(members):
            # Get the Wikipedia slug for the member's page
            wiki_slug = member['wiki'].replace('https://nl.wikipedia.org/wiki/', '').replace('https://fr.wikipedia.org/wiki/', '')
            # Make a request to the Wikipedia API to get the page properties
            r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={wiki_slug}&format=json').json()
            # Get the pages from the API response
            pages = r["query"]["pages"]
            # If there are pages returned
            if pages.keys():
                # Get the page properties for the first page
                page_zero_props = pages[list(pages.keys())[0]]['pageprops']
                # If the page has a Wikibase item ID
                if 'wikibase_item' in page_zero_props:
                    # Get the Wikibase item for the page
                    item = pywikibot.ItemPage(repo, page_zero_props['wikibase_item'])
                    # Add the Wikibase item ID to the member's data
                    member['wikibase_item'] = page_zero_props['wikibase_item']
                    # If the item has a P21 (gender) claim
                    if 'P21' in item.get()['claims']:
                        # Get the gender label in English
                        gender = item.get()['claims']['P21'][0].getTarget().get()['labels']['en']
                        # Add the gender label to the member's data
                        member['gender'] = gender
                        # Continue to the next member
                        continue
            # If the member does not have a gender label, set it to 'X'
            member['gender'] = 'X'
        # Open the output JSON file
        with open('outfile.json', 'w+') as op:
            # Write the updated members data to the output JSON file
            json.dump(members, op, ensure_ascii=False)
                    
if __name__ == "__main__":
    main()