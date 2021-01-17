import io, os

num_cluster = 0
num_mention = 0

file_dir = '..' + os.sep + 'predicted' + os.sep + 'dcoref' + os.sep + 'conll'
for split in os.listdir(file_dir):
    for filename in os.listdir(file_dir+os.sep+split):
        file_cluster = 0
        existed_cluster = []
        with open(file_dir+os.sep+split+os.sep+filename, encoding='utf-8') as f:
            lines = f.read().split('\n')
            for line in lines:
                if '\t' not in line:
                    continue
                fields = line.split('\t')
                if fields[-1] == '_':
                    continue
                coref_fields = fields[-1].split('|')
                for coref in coref_fields:
                    if '(' in coref:
                        cluster = coref.strip('(').strip(')')
                        num_mention += 1
                        if cluster not in existed_cluster:
                            existed_cluster.append(cluster)
                            file_cluster += 1
        num_cluster += file_cluster

print(f'Number of coref chains: {num_cluster}')
print(f'Number of mentions: {num_mention}')
