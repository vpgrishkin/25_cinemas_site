import os
import logging

from flask import Flask, render_template, jsonify, redirect, request, json, send_from_directory
from werkzeug.contrib.cache import FileSystemCache

import cinemas


ENV_DEBUG = os.environ.get('DEBUG') == 'True'
PORT = int(os.environ.get('PORT', 5000))
CACHE_TIMEOUT = 60 * 60 * 12
cache = FileSystemCache('.cachedir', default_timeout=CACHE_TIMEOUT)
app = Flask(__name__)


@app.route('/')
def output_static_index_page():
    return render_template('films_list.html')

@app.route('/api')
def output_static_api_page():
    return render_template('api.html')


@app.route('/movies', methods=['GET'])
def output_movies():
    movies_json = cache.get('movies_json')
    if movies_json is None:
        afisha_page = cinemas.fetch_afisha_page()
        movies_from_afisha = cinemas.parse_afisha_list(afisha_page)
        movies_json = json.jsonify(movies_from_afisha)
        cache.set('movies_json', movies_json)
    return movies_json


@app.route('/movie_info', methods=['GET'])
def output_movie_info():
    movie_url = request.args.get('movie_url')
    logging.info('[%d/%d] Get "%s":', movie_url)

    movie_info_json = cache.get(movie_url)
    if movie_info_json is None:
        logging.info('[%d/%d] No cache "%s":', movie_url)
        movie_info = cinemas.fetch_afisha_movie_description(movie_url)
        movie_info['rating'] = cinemas.fetch_movie_rating(movie_info['name'])
        movie_info_json = jsonify(movie_info)
        cache.set(movie_url, movie_info_json)
    return movie_info_json


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=ENV_DEBUG)
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s# %(levelname)-8s [%(asctime)s] %(message)s',
        datefmt=u'%m/%d/%Y %I:%M:%S %p'
    )
