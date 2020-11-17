"""
Convert XML output of Stanford CoreNLP to CoNLL 2012 format.

$ ./corenlp.sh -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref \
		-output.printSingletonEntities true \
		-file /tmp/example.txt
$ python3 corenlpxmltoconll2012.py example.txt.xml > example.conll`

edited from andreasvc: https://gist.github.com/andreasvc/6bf9e10b2e6956ce32fb777e7efe99cb
"""
import re
import sys
from lxml import etree


def gettext(node):
	"""Safely read text of lxml node."""
	return '-' if node is None else node.text


def splitparse(parse):
	"""Split PTB parse tree into parse bits."""
	parse = parse.replace('\n', ' ')
	result = re.sub(r'\([^\s()]+ [^\s()]+\)([^(]*)', r'*\1\n', parse)
	return result.replace(' ', '').splitlines()


def nerspans(tokens):
	"""Create NER spans in CoNLL 2012 format from token-based NER labels.

	Single token names: ['(PERSON)']; Multiword names: ['(ORG*', '*', '*)']
	Will not create nested NER spans such as (University of (California))."""
	result = ['*'] * len(tokens)
	nerlabels = [gettext(token.find('./NER')) for token in tokens]
	for n, ner in enumerate(nerlabels):
		if ner == '-' or ner == 'O':
			continue
		elif n == 0 or nerlabels[n - 1] != ner:
			if n == len(tokens) - 1 or nerlabels[n + 1] != ner:
				result[n] = '(%s)' % ner
			else:
				result[n] = '(%s*' % ner
		elif n == len(tokens) - 1 or nerlabels[n + 1] != ner:
			result[n] = '*)'
	return result


def conv(filename):
	"""Read CoreNLP XML file and print in CoNLL 2012 format on stdout."""
	doc = etree.parse(filename).getroot().find('./document')
	genre = filename.split('/')[-1].split('.')[0].split('_')[1]
	name = filename.split('/')[-1].split('.')[0].split('_')[-1]
	docid = f'{genre}/{name}'
	partid = 0
	result = []
	for sent in doc.find('./sentences'):
		parsebits = splitparse(sent.find('./parse').text)
		nerbits = nerspans(sent.find('./tokens'))
		result.append([
					[docid,
					str(partid),
					str(int(token.get('id', '-'))-1),
					gettext(token.find('./word')),
					gettext(token.find('./POS')),
					parsebits[n],
					'-',  # predicate lemma
					'-',  # predicate frameset ID
					'-',  # word sense
					gettext(token.find('./Speaker')),
					nerbits[n],
					'']  # coref chain
				for n, token in enumerate(sent.find('./tokens'))])

	for clusterid, coref in enumerate(doc.find('./coreference')):
		for mention in coref:
			sentid = int(mention.find('./sentence').text) - 1
			start = int(mention.find('./start').text) - 1
			end = int(mention.find('./end').text) - 1
			if start == end - 1:
				result[sentid][start][-1] += '(' + str(clusterid) + ')|'
			else:
				result[sentid][start][-1] += '(' + str(clusterid) + '|'
				result[sentid][end - 1][-1] += str(clusterid) + ')|'

	print('#begin document (%s); part %03d' % (docid, partid))
	for chunk in result:
		for line in chunk:
			line[-1] = line[-1].rstrip('|') or '-'
			print('\t'.join(line))
		print()
	print('#end document')


if __name__ == '__main__':
	conv(sys.argv[1])
