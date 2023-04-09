# Import necessary libraries
import json
import requests
import pywikibot
import tqdm

# Set the site and repository for Wikipedia
site = pywikibot.Site("nl", "wikipedia")
repo = site.data_repository()

def main():
    # Load the data from the JSON file
    filename = 'data/composition/52.json'
    with open(filename, 'r') as fp:
        members = json.load(fp)
    
    # Iterate through each member and try to find their photo URL
    for member in tqdm.tqdm(members):
        if 'photo_url' in member:
            continue
        
        # First try to find the photo on Wikipedia
        wiki_slug = member['wiki'].replace('https://nl.wikipedia.org/wiki/', '').replace('https://fr.wikipedia.org/wiki/', '')
        r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={wiki_slug}&format=json').json()
        pages = r["query"]["pages"]
        if pages.keys():
            page = pages[list(pages.keys())[0]]['pageprops']
            if 'page_image_free' in page:
                r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&generator=images&prop=imageinfo&titles={wiki_slug}&iiprop=url|dimensions|mime&format=json').json()
                for image in r['query']['pages'].values():
                    if page['page_image_free'] in image['imageinfo'][0]['url']:
                        member['photo_url'] = image['imageinfo'][0]['url']
                        break
        
        # If the photo is not found on Wikipedia, try to find it on Wikidata
        if 'photo_url' not in member and 'wikibase_item' in member:
            item = pywikibot.ItemPage(repo, member['wikibase_item'])
            image_object = item.page_image()
            if image_object:
                member['photo_url'] = image_object.get_file_url()

        # Save the updated data to the JSON file
        with open(filename, 'w') as fp:
            json.dump(members, fp, ensure_ascii=False)

if __name__ == "__main__":
    main()