import logging
from bs4 import BeautifulSoup
import random
import json

import requests
from requests.exceptions import RequestException


AFISHA_URL = 'https://www.afisha.ru/msk/schedule_cinema/'
KINOPOISK_URL = 'https://www.kinopoisk.ru/index.php'
PROXY_URL = 'http://www.freeproxy-list.ru/api/proxy'
TIMEOUT = 5
NUM_MOVIES = 10
PARSE_MOVIES_LIMIT = 30
CINEMAS_COUNT_LIMIT = 1
AGENT_LIST = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12 AppleWebKit/602.4.8',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64)',
    'Opera/9.80 (Windows NT 6.2; WOW64) Presto/2.12.388 Version/12.17'
]


def fetch_afisha_page():
    return requests.get(AFISHA_URL).text


def parse_afisha_list(raw_html):
    soup = BeautifulSoup(raw_html, 'lxml')

    movies_titles_tags = soup.find_all('div', {'class': 'm-disp-table'})

    movie_details = {}
    for movie_title_tag in movies_titles_tags[:PARSE_MOVIES_LIMIT]:
        movie_title = movie_title_tag.find('a').text
        cinemas_count = len(movie_title_tag.parent.find_all('td', {'class': 'b-td-item'}))
        movie_url = movie_title_tag.find('h3', {'class': 'usetags'}).find('a').get('href')
        movie_details[movie_title] = {'cinemas_count': cinemas_count, 'movie_url':movie_url}

    return movie_details


def fetch_kinopoisk_movie_page(movie_title, proxy_list):
    params = {'kp_query': movie_title, 'first': 'yes'}

    while True:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Agent:{}'.format(random.choice(AGENT_LIST))
        }
        proxy_ip = random.choice(proxy_list)
        proxy = {'http': proxy_ip}

        logging.info('Proxy: %s', proxy_ip)

        try:
            request = requests.Session().get(
                KINOPOISK_URL,
                params=params,
                headers=headers,
                proxies=proxy,
                timeout=TIMEOUT
            )
        except(requests.exceptions.ConnectTimeout,
               requests.exceptions.ConnectionError,
               requests.exceptions.ProxyError,
               requests.exceptions.ReadTimeout):
            logging.exception('Connect error.')
        else:
            break

    return request.text


def parse_kinopoisk_rating(raw_html):
    try:
        soup = BeautifulSoup(raw_html, 'lxml')
        rating = soup.find('span', {'class': 'rating_ball'}).text
    except AttributeError:
        rating = None
    return rating


def fetch_movie_rating(movie_title):
    proxies_list = get_proxies_list()
    logging.info('[%d/%d] Get "%s" page...', movie_title)
    kinopoisk_page = fetch_kinopoisk_movie_page(movie_title, proxies_list)
    return parse_kinopoisk_rating(kinopoisk_page)


def fetch_afisha_movie_description(afisha_movie_url):
    response_content = requests.get(afisha_movie_url).text
    soup_data = BeautifulSoup(response_content, 'html.parser')
    response_json = soup_data.find(attrs={"type": "application/ld+json"}).text
    movie_description_raw_dict = json.loads(response_json)
    movie_description = {}
    movie_description['description'] = movie_description_raw_dict['description']
    movie_description['image'] = movie_description_raw_dict['image']

    return movie_description


def get_proxies_list():
    params = {'anonymity': 'true', 'token': 'demo'}
    request = requests.get(PROXY_URL, params=params).text
    proxies_list = request.split('\n')
    return proxies_list


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s# %(levelname)-8s [%(asctime)s] %(message)s',
        datefmt=u'%m/%d/%Y %I:%M:%S %p'
    )
