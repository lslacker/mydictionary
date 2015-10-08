__author__ = 'lslacker'

import requests
import logging
from abc import ABCMeta, abstractmethod
from lxml import html, etree
from collections import defaultdict
import subprocess

logger = logging.getLogger(__name__)


class Parser(metaclass=ABCMeta):

    @abstractmethod
    def parse(self, text):
        pass


class LParser(Parser):

    def parse(self, text):
        tree = html.fromstring(text)
        pos_headers = tree.xpath('//*[@id="dataset-american-english"]//div[@class="pos-header"]')
        pos_bodies = tree.xpath('//*[@id="dataset-american-english"]//div[@class="pos-body"]')
        pos_bodies1 = tree.xpath('//*[@id="dataset-american-english"]//span[@class="runon-body"]')
        pos_bodies += pos_bodies1
        results = defaultdict(list)

        if pos_headers:
            for idx, header in enumerate(pos_headers):
                es = header.findall('h3/span')
                word = ''
                for e in es:
                    word += '{} '.format(e.text_content())
                es = header.xpath('.//span[@class="pron"]')

                for e in es:
                    word += '{}'.format(e.text_content())
                logger.info(word)
                mp3 = header.xpath('.//span/@data-src-mp3')[0] or None
                sub_text = etree.tostring(pos_bodies[idx], pretty_print=True).decode('utf-8')
                result = self.parse(sub_text)
                results[word] += result

            return results, mp3
        else:

            blocks = tree.xpath('//span[@class="def-block"]')
            temp_result = []
            for block in blocks:
                definitions = block.xpath('.//span[@class="def"]')
                examples = block.xpath('.//span[@class="eg"]')

                definitions = [definition.text_content() for definition in definitions]
                definition = definitions[0] if definitions else ''

                examples = [example.text_content() for example in examples]

                temp_result += [(definition, examples)]

            return temp_result


class Search:

    LOOKUP_LINK = 'http://dictionary.cambridge.org/dictionary/english/{}'

    def __init__(self, parser):
        self.parser = parser

    def search(self, text):
        search_link = self.LOOKUP_LINK.format(text)

        r = requests.get(search_link)
        results, mp3 = self.parser.parse(r.text)

        r = requests.get(mp3)
        with open('test.mp3', 'bw') as f:
            f.write(r.content)

        for word, blocks in results.items():
            print(word)
            for definition, examples in blocks:
                print('- {}'.format(definition))
                for example in examples:
                    print('    > {}'.format(example))
            print('\n')


def awaiting_answer(text):
    return input(text)


def main():
    lxml_parser = LParser()
    searcher = Search(lxml_parser)
    searcher.search('raid')
    # while True:
    #     text = input("Search English: ")
    #     try:
    #         searcher.search(text)
    #         yes_no = awaiting_answer("Speak?")
    #         if yes_no.upper() in ['Y', 'YES']:
    #             subprocess.call("play test.mp3", shell=True)
    #             yes_no = awaiting_answer("Again?")
    #             while yes_no.upper() in ['Y', 'YES']:
    #                 subprocess.call("play test.mp3", shell=True)
    #                 yes_no = awaiting_answer("Again?")
    #     except:
    #         print('{} not found, please check'.format(text))
if __name__ == '__main__':
    main()
