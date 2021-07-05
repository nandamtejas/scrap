from flask import Flask, render_template, redirect
import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(filename="newfile.log", filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
BASE_URL = "https://www7.animeseries.io/"

def scrapped_data():
    try:
        # Scrape data from url 'https://www7.animeseries.io/'
        html_url = BASE_URL
        html_response = requests.get(html_url, stream=True)
        soup = BeautifulSoup(html_response.text, 'html.parser')

        # Thumbnail image urls
        blocks = soup.find_all('div',attrs={'class':"thumb_anime"})
        thumbnail_url = []
        for block in blocks:
            a = re.findall("'([a-z].*)'",str(block))
            thumbnail_url.append(*a)


        # Anime Name
        epi_name = soup.find_all('div', attrs={'class': "name"})
        names = [str(name).split(">")[-2].split("<")[0] for name in epi_name]

        # episode number
        epi_number = soup.find_all('div', attrs={'class':'episode'})
        episodeno = [str(n).split(">")[-2].split("<")[0] for n in epi_number]

        # episode links
        epi_links = []
        for name in names:
            ss = soup.find_all('a', attrs={'title':name})
            a = re.findall('href="([a-z\/\.].*)" ',str(ss))
            if a != []:
                epi_links.append(a[0])
            else:
                epi_links.append("")

        # time_ago
        time_ago = soup.find_all('span',attrs={'class': 'time_ago'})
        time_ago = [str(n).split(">")[-2].split("<")[0] for n in time_ago]

        # create a dictionary
        # name
        # episode number
        # episode link
        # thumb image
        # video file download
        output = []
        for name, epi_no, epi_link, thumb_img, ago in zip(names,episodeno, epi_links, thumbnail_url,time_ago):
            if epi_link != []:
                output.append(
                    {
                        "anime_name": name,
                        "episode_link": epi_link,
                        "episode_number": epi_no,
                        "thumb_img": thumb_img,
                        "time_ago": ago
                    }
                )
        return output
    except Exception as e:
        logger.error(str(e))

# Create a web app to show all the scraped data
@app.get('/')
def index():
    try:
        data = scrapped_data()
        return render_template("base.html",datas=data)
    except EOFError as err:
        logger.error(str(err))

@app.get("/download/<name>")
def download(name):
    try:
        data = scrapped_data()
        filtered_data = list(filter(lambda n: n['anime_name'] == name, data))
        episode_link = BASE_URL + filtered_data[0]['episode_link']
        new_request = requests.get(episode_link,stream=True)
        new_soup = BeautifulSoup(new_request.content,'html.parser')
        red_lnk = new_soup.find_all('a',attrs={'class':"play-video player selected"})
        # extract link
        a = re.findall('data-video="([\S].*)">',str(red_lnk[0]))[0]
        return redirect(f"https:{a}")
    except IndexError as e:
        logger.warn(str(e))

if __name__ == "__main__":
    app.run(debug=False)