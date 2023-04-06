# This script retrieves photos of members from Wikipedia and Wikidata
# It takes a json file as input and updates it with photo urls
# If a member already has a photo_url, it skips that member
# If a member has a wikipedia page, it tries to get the photo from there
# If not, it tries to get the photo from the wikidata item page

import json
import requests
import pywikibot
import tqdm

site = pywikibot.Site("nl", "wikipedia")
repo = site.data_repository()

def main():
    # Load json file with members
    filename = 'data/composition/52.json'
    with open(filename, 'r') as fp:
        members = json.load(fp)

    # Loop through members
    for member in tqdm.tqdm(members):
        # Skip members that already have a photo_url
        if 'photo_url' in member:
            continue

        # First try wikipedia, then wikidata
        wiki_slug = member['wiki'].replace('https://nl.wikipedia.org/wiki/', '').replace('https://fr.wikipedia.org/wiki/', '')
        r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={wiki_slug}&format=json').json()
        pages = r["query"]["pages"]
        if pages.keys():
            page = pages[list(pages.keys())[0]]['pageprops']
            if 'page_image_free' in page:
                # Get image info from wikipedia
                r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&generator=images&prop=imageinfo&titles={wiki_slug}&iiprop=url|dimensions|mime&format=json').json()
                for image in r['query']['pages'].values():
                    if page['page_image_free'] in image['imageinfo'][0]['url']:
                        member['photo_url'] = image['imageinfo'][0]['url']
                        break

        # If no photo url yet and member has a wikidata item, try to get the photo from there
        if 'photo_url' not in member and 'wikibase_item' in member:
            item = pywikibot.ItemPage(repo, member['wikibase_item'])
            image_object = item.page_image()
            if image_object:
                member['photo_url'] = image_object.get_file_url()

        # Save updated member info to json file
        with open(filename, 'w') as fp:
            json.dump(members, fp, ensure_ascii=False)

if __name__ == "__main__":
    main()