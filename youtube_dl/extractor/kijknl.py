# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError
import json
import re

class KijkNLIE(InfoExtractor):
    #_VALID_URL = r'https?://(?:www\.)?yourextractor\.com/watch/(?P<id>[0-9]+)'
    _VALID_URL = r'https?://(?:www\.)?kijk\.nl/(?:films/video/[^/]*/|programmas/[^/]*/[^/]*/seizoen/[^/]*/afleveringen/video/[^/]*/)(?P<id>[A-Za-z0-9]+)'
    _TESTS = [
        {
            'url': 'https://kijk.nl/programmas/ik-ook-van-jou/Wp2Fizct6mD/seizoen/113154600199/afleveringen/video/empty_episode-ik-ook-van-jou-s1-e18-2013-09-18/IigojlxqRQYg',
            'info_dict': {
                'id': 'IigojlxqRQYg',
                'ext': 'mp4',
                'title': 'Ik ook van Jou',
                # TODO more properties, either as:
                # * A value
                # * MD5 checksum; start the string with md5:
                # * A regular expression; start the string with re:
                # * Any Python type (for example int or float)
            }
        },
        {
            'url': 'https://kijk.nl/films/video/the-bounty-hunter/CQvs74EAaJj',
            'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
            'info_dict': {
                'id': 'CQvs74EAaJj',
                'ext': 'mp4',
                'title': 'Video title goes here',
                'thumbnail': r're:^https?://.*\.jpg$',
                # TODO more properties, either as:
                # * A value
                # * MD5 checksum; start the string with md5:
                # * A regular expression; start the string with re:
                # * Any Python type (for example int or float)
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        #all of the webpages have a json blob for NEXT that contains the video info
        next_json = self._search_regex(r'<script[^>]+id="__NEXT_DATA__"[^>]*>([^<]+)<', webpage, 'next_json', fatal=True)

        #dig a bit down into the json
        parsed_json = json.loads(next_json)
        video_info = parsed_json['props']['pageProps']['video']

        #if the video is a tv program. I think this is how to differentiate
        if(parsed_json['page'] == "/programmas/format"):
            type = 'TvShow'
        elif(parsed_json['page'] == "/movies"):
            type = 'Movie'
        else:
            raise ExtractorError("Unknown page type '%s'. Needs investigation. Exiting" % parsed_json['page'])

        if(type == 'TvShow'):
            metadata_info = parsed_json['props']['pageProps']['format']

            # Get some metadata for the program.
            title = metadata_info['title']
            description = metadata_info['description']
            seasonNumber = video_info['seasonNumber']
            episodeNumber = video_info['tvSeasonEpisodeNumber']
        elif(type == 'Movie'):
            title = video_info['title']
            description = video_info['shortDescription']

        formats = list()
        subtitles = dict()

        if(len(video_info['media']) > 1):
            #If the length of the media list is more than one, raise an error,
            # because i haven't seen an example of it yet and don't know what it means.
            raise ExtractorError("There is more than one media entry in the list. Don't know how to handle this...Exiting")

        for m in video_info['media'][0]['mediaContent']:
            # In this list are a bunch of urls pointing to manifest files and subtitle files

            #Not sure what the typename does, so if we see a new one raise an error
            if(m['__typename'] != "MediaFile"):
                raise ExtractorError("New __typename '%s' found. Exiting for investigation" % m['__typename'])

            mediaUrl = m['sourceUrl']
            r = re.compile(r'.([A-Za-z0-9]+)$')
            m = r.search(mediaUrl)
            extension = m.group(1)


            if(extension == "vtt"):
                #assume the language is dutch because we haven't seen a way to indicate otherwise
                # We only expect 1 subtitle file right now. If there's more we need to investigate
                if(len(subtitles.keys()) > 0):
                    raise ExtractorError("More than one subtitle found. We don't know how to handle this yet. Exiting")

                subtitles['nl'] = [ { 'ext': 'vtt', 'url': mediaUrl} ]
            elif(extension == "ismc"):
                print("Warning: Ignoring ismc manifest")
            elif(extension == "mpd"):
                formats.extend(self._extract_mpd_formats(mediaUrl, video_id))
            elif(extension == 'm3u8'):
                #formats.extend(self._extract_m3u8_formats(mediaUrl, video_id))
                print("Warning: Ignoring m3u8 manifest")
            else:
                raise ExtractorError("Unknown media url extension '%s' found. Needs investigation. Exiting" % extension)

        result = {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'subtitles': subtitles
            # TODO more properties (see youtube_dl/extractor/common.py)
        }

        if(type == 'TvShow'):
            result['season_number'] = seasonNumber
            result['episode_number'] = episodeNumber

        return result
