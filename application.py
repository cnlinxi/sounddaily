import logging
import time
import re
import requests
from bs4 import BeautifulSoup

from flask import Flask

logger = logging.getLogger(__name__)

ROOT_URL = 'https://arxiv.org'
CAT_SOUND = '/list/cs.SD/recent'
CAT_AS = '/list/eess.AS/recent'
CAT_CL = '/list/cs.CL/recent'
CAT_MM = '/list/cs.MM/recent'


def get_arxiv_paper_list(paper_list_url):
    is_failed = True
    failed_counter = 0
    try:
        papers = []
        while is_failed and failed_counter < 3:
            response = requests.get(paper_list_url)
            if response.status_code == 200:
                is_failed = False
            else:
                time.sleep(1)
                failed_counter += 1
                continue
            list_html_doc = response.content
            list_soup = BeautifulSoup(list_html_doc, 'lxml')
            # pages = list_soup.select('body div div#dlpage')[0].dl
            is_start_paper = False
            paper = None
            for x in list_soup.select('body div div#dlpage')[0].dl.children:
                if (x is None) or (not str(x).strip('\r\n ')):
                    continue
                if not is_start_paper:
                    paper = {}
                    match_obj = re.match(r'.*?<span class="list-identifier"><a href="(.*?)" title="Abstract">.*?',
                                         str(x), re.M | re.I)
                    if match_obj is not None:
                        paper['link'] = ROOT_URL + str(match_obj.group(1)).strip('\r\n ')
                        is_start_paper = True
                else:
                    match_obj = re.match(
                        r'.*?<span class="descriptor">Title:</span>(.*?)</div>.*?<span class="descriptor">Authors:</span>(.*?)</div>.*?',
                        str(x).replace('\n', ''), re.M | re.I)
                    if match_obj is not None:
                        paper['title'] = match_obj.group(1).strip('\r\n ')
                        author_links = match_obj.group(2).replace(',', '').split('</a>')
                        authors = [x.split('">')[-1].strip('\r\n ') for x in author_links]
                        authors = [x for x in authors if len(x) > 0]
                        paper['authors'] = ', '.join(authors)
                        papers.append(paper)
                        is_start_paper = False
    except Exception as e:
        logger.error('error to get paper list, exception: {}'.format(e))
        return []

    return papers


def get_arxiv_abstract(papers):
    papers_ = []
    for paper in papers:
        try:
            failed_counter = 0
            is_failed = True
            while is_failed and failed_counter < 3:
                response = requests.get(paper['link'])
                if response.status_code == 200:
                    is_failed = False
                else:
                    time.sleep(1)
                    failed_counter += 1
                    continue
                abstract_html_doc = response.content
                match_obj = re.match(r'.*?<span class="descriptor">Abstract:</span>(.*?)</blockquote>.*?',
                                     str(abstract_html_doc).replace('\n', ''), re.M | re.I)
                if match_obj is not None:
                    abstract = match_obj.group(1).strip('\r\n ').replace('\\n', '')
                    abstract = ' '.join(abstract.split(' ')[:20]) + '...'
                    paper['abstract'] = abstract
        except Exception as e:
            logger.error('error to get {} abstract, exception: {}'.format(paper, e))

        papers_.append(paper)
        time.sleep(0.5)

    return papers_


app = Flask(__name__)


@app.route('/')
def hello():
    return 'sound daily'


@app.route('/sound')
def sound():
    papers = get_arxiv_paper_list(ROOT_URL + CAT_SOUND)
    papers = get_arxiv_abstract(papers)
    return str(papers)


@app.route('/as')
def audio_process():
    papers = get_arxiv_paper_list(ROOT_URL + CAT_AS)
    papers = get_arxiv_abstract(papers)
    return papers


@app.route('/multimedia')
def multimedia():
    papers = get_arxiv_paper_list(ROOT_URL + CAT_MM)
    papers = get_arxiv_abstract(papers)
    return papers


@app.route('/nlp')
def nlp():
    papers = get_arxiv_paper_list(ROOT_URL + CAT_MM)
    papers = get_arxiv_abstract(papers)
    return papers


if __name__ == '__main__':
    app.run()
