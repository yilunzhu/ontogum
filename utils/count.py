import io, os
import re
from collections import defaultdict

num_cluster = 0
num_mention = 0
num_chain = 0

genre_cluster = defaultdict(int)
genre_mention = defaultdict(int)
genre_chain = defaultdict(int)

file_dir = '..' + os.sep + 'out' + os.sep + 'conll'
for filename in os.listdir(file_dir):
    genre = filename.split('_')[1]
    file_cluster = 0
    file_chain = 0
    existed_cluster = []
    with open(file_dir+os.sep+filename, encoding='utf-8') as f:
        lines = f.read().split('\n')
        for line in lines:
            if '\t' not in line:
                continue
            fields = line.split('\t')
            if fields[-1] == '_':
                continue

            for coref in re.findall('\([0-9]+', fields[-1]):
                if coref:
                    cluster = coref.strip('(').strip(')')
                    genre_mention[genre] += 1
                    num_mention += 1
                    if cluster in existed_cluster:
                        file_chain += 1
                    if cluster not in existed_cluster:
                        existed_cluster.append(cluster)
                        file_cluster += 1
        a = 1
    genre_cluster[genre] += file_cluster
    genre_chain[genre] += file_chain

    num_cluster += file_cluster
    num_chain += file_chain

print(f'Number of coref clusters: {num_cluster}')
print(f'Number of coref chains: {num_chain}')
print(f'Number of mentions: {num_mention}')
print(f'Genre-wise coref clusters: {genre_cluster}')
print(f'Number of coref chains: {genre_chain}')
print(f'Genre-wise mentions: {genre_mention}')
