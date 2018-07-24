#!/usr/bin/env python

import logging
import multiprocessing as mp
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
import tldextract
from bs4 import BeautifulSoup

import database
import hundlers

WORD = None
DOMAIN = None
regex = "(.*"+str(DOMAIN)+"\.com.*)|(^\/[a-z].*$)"

check_urls = set()
m = mp.Manager()  # Manager of multiprocessing
q = m.JoinableQueue()  # queue of manager
urls_save = m.dict()  # Shared list contain url with flag 'True'
executed = {}  # task compilte
non_executed = {}  # task don't executed


class Task(object):
    """Class implementation Task

     Attributes:

         url (str): link for task
         success (bool): status of task
         positive (bool): status of founded pattern

    """
    def __init__(self, url):
        self.url = url
        self.title = None
        self.success = False
        self.positive = False

    def run_task(self):
        """Run task.
        Returns:
            url(str): if task done
            None : if task don't executed
        """
        result = process(self)
        if result:
            self.success = True
            q.task_done()
            executed[self] = self.url
            self.add_queue(result)
            return self.url
        else:
            non_executed[self] = self.url
            return None

    def add_queue(self, urls):
        """Add new url in queue"""
        # [q.put(url) for url in result if url]
        for url in urls:
            if url not in check_urls:
                q.put(url)

    def add_db(self):
        """Add Task in database if flag is positive"""
        if self.positive:
            result = database.add_db(url=self.url, title=self.title)
            return result
        return 'Not positive'


def get_soup(url):
    """This method allow get a html body of url.
    Args:
        url (str): current link.

    Returns:
        soup : html body of url
        r : requests object of url.
        False, None : returns if status code is not 200
    """
    try:
        r = requests.get(url, headers=hundlers.USER_AGENT, timeout=4)
        if r.status_code != 200:
            return False, None
        soup = BeautifulSoup(r.text, "lxml")
        return soup, r
    except (requests.ConnectionError, requests.Timeout, UnicodeError,
            requests.RequestException, Exception) as e:
        print(str(e))
        return False, None


def process(task):
    """Get urls from domain (only external domain URLs) and added urls in queue.
    Also checks on pattern.
    Args:
        task (Task) : current link for process.
    Returns:
        find_urls(set): contain all internal domain URLs.
    """
    find_urls = set()
    soup, r = get_soup(task.url)
    print('working url page', task.url)
    if not soup or soup is None:
        return(None)
    pos = positive(soup=soup, task=task)
    print(pos)
    for tag in soup.findAll('a', href=re.compile(regex)):
        try:
            link = urljoin(r.url, tag['href'])
            find_urls.add(link)
        except ValueError as e:
            continue
    print('url page done', task.url, 'count of urls founded', len(find_urls))
    return find_urls


def positive(soup, task):
    """Return status of searching pattern in url body
    Args:
        url (str): Main domain.
        soup : body of url
        pattern(regexp): pattern for searching
    Return:
        result(str): staus of operation.
     """
    if (soup.find_all(string=re.compile(WORD, re.IGNORECASE), limit=1)
            and task.url not in urls_save):
        title = '...'
        if soup.title.string is not None:
            title = soup.title.string[:50] + '...'
        urls_save[task.url] = title
        task.positive = True
        task.title = title
        task.add_db()
        return('Find pattern')
    return('Not found')


def check_for_tasks():
    """This method form list of task for Pool
    Return:
        list_tasks(list): list of current task
    """
    list_tasks = []
    q_size = q.qsize() if q.qsize() < 400 else 200
    for __ in range(q_size):
        url = q.get()
        task = Task(url=url)
        list_tasks.append(task)
        check_urls.add(url)
    return list_tasks


def run(processes):
    """The main loop of tasks where everything happens.
    Args:
        prosseses(int) : number of workers
    """
    while True:
        tasks = check_for_tasks()
        if not len(tasks):
            continue
        with mp.Pool(processes=processes) as pool:
            result = pool.map_async(Task.run_task, tasks)
            print(result.get())
            pool.close()
            pool.join()
            print(len(tasks))
            print(q.qsize(), 'size of queue')
            print(len(check_urls), 'checked pages')
            print(len(urls_save), 'urls_save')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: {0} URL ...".format(Path(sys.argv[0]).name))
        sys.exit(1)
    WORD = sys.argv[2]
    URL = sys.argv[1]
    processes = 25
    DOMAIN = tldextract.extract(URL)
    q.put(URL)
    run(processes)
