import io, os, sys


def write_file(dir, doc):
    with io.open(dir, 'w', encoding='utf-8') as f:
        f.write(doc)


conll_dir = sys.argv[1]
out_dir = sys.argv[2]

genres = ["academic", "bio", "fiction", "interview", "news", "voyage", "whow", "reddit", "conversation", "speech",
          "textbook", "vlog"]
docs_by_genre = {g:'' for g in genres}
docs_train = ''
docs_dev = ''
docs_test = ''

for split in os.listdir(conll_dir):
    for filename in os.listdir(conll_dir+os.sep+split):
        with io.open(conll_dir+os.sep+split+os.sep+filename, encoding='utf-8') as f:
            cur_genre = filename.split('_')[1]
            lines = f.read()
            if split == 'train':
                docs_train += lines + '\n'
            elif split == 'test':
                docs_test += lines + '\n'
            else:
                docs_dev += lines + '\n'
                docs_by_genre[cur_genre] += lines + '\n'

write_file(out_dir+os.sep+'train.gum.conll', docs_train)
write_file(out_dir+os.sep+'test.gum.conll', docs_test)
write_file(out_dir+os.sep+'dev.gum.conll', docs_dev)
for g, doc in docs_by_genre.items():
    write_file(out_dir+os.sep+f'dev.gum.{g}.conll', doc)
print('Done.')
