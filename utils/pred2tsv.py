import io, os
import json

print('Processing...')
for filename in os.listdir('../out/preds/json'):
    f_name = filename.split('/')[-1]
    print(f_name)

    count = 0
    merged = 0
    tsv = []
    with io.open('../dataset/preds/json'+os.sep+f_name, encoding='utf-8') as f:
        tok_map = {}
        for example_num, line in enumerate(f.readlines()):
            example = json.loads(line)
            tok_count = 1
            prev_sent = 1

            # get token and sentence information
            toks = [y for x in example['sentences'] for y in x]
            for i in range(len(example['sentence_map'])):
                cur_subtok = example['subtoken_map'][i]
                cur_sent = example['sentence_map'][i] + 1
                if cur_sent != prev_sent:
                    tok_count = 1
                    prev_sent = cur_sent
                tok_map[i] = {'sent': cur_sent, 'tok': toks[i], 'sub_tok': example['subtoken_map'][i], 'tok_num': tok_count}
                tok_count += 1

                # if cur_subtok not in tok_map.keys():
                #     if toks[i] == '[CLS]':
                #         tok_map[cur_subtok] = {'sent': example['sentence_map'][i], 'tok': ''}
                #     else:
                #         tok_map[cur_subtok] = {'sent': example['sentence_map'][i], 'tok': f'{toks[i]}'}
                # else:
                #     if toks[i] != '[SEP]':
                #         tok_map[cur_subtok]['tok'] += toks[i].replace('##', '')

            # generate mention spans and which span corefers to which one
            # coref {1:2, 2:3}
            # mentions {331:1, 332:1, 339:2}
            # mention_start {1:True}
            # mention_start_pos {1:331}
            predicted_clusters = example['predicted_clusters']
            coref, mentions, mention_start, mention_start_pos = {}, {}, {}, {}
            mention_num = 1
            for cluster in predicted_clusters:
                prev_mention_num = 0
                for m in cluster:
                    start, end = m[0], m[-1]
                    span = [x for x in range(int(start), int(end)+1)]
                    for s in span:
                        if s not in mentions.keys():
                            mentions[s] = []
                        mentions[s].append(mention_num)

                    if mention_num > prev_mention_num:
                        coref[prev_mention_num] = mention_num
                    mention_start[mention_num] = True
                    mention_start_pos[mention_num] = tok_map[start]
                    prev_mention_num = mention_num
                    mention_num += 1

            # generate tsv format
            prev_sent = '0'
            sent, tok_count = [], 0
            for i in tok_map.keys():
                cur_sent = tok_map[i]['sent']
                cur_tok = tok_map[i]['tok']
                tok_count += 1

                cur_line = ['_', '_', cur_tok, '_', '_', '_', '_']
                if i in mentions.keys():
                    for j in mentions[i]:
                        cur_line[-4] += f'abstract[{j}]|'
                        cur_line[-3] += f'new[{j}]|'
                        if mention_start[j]:
                            if j in coref.keys():
                                cur_line[-2] += f'coref|'
                                cur_line[-1] += f'{tok_map[i]["sent"]}-{tok_map[i]["tok_num"]}[{j}_{coref[j]}]|'
                                mention_start[j] = False
                    for n in range(-4, 0):
                        cur_line[n] = cur_line[n].strip('_').strip('|') if cur_line[n] != '_' else '_'

                        # cur_line[-4], cur_line[-3], cur_line[-2], cur_line[-1] = cur_line[-4].strip('_').strip('|'), cur_line[-3].strip('_').strip('|'), cur_line[-2].strip('_').strip('|'), cur_line[-1].strip('_').strip('|')
                if cur_sent != prev_sent:
                    tsv.append(sent)
                    sent = []
                    tok_count = 1
                cur_line[0] = f'{cur_sent}-{tok_count}'
                sent.append(cur_line)

                prev_sent = cur_sent

    # clean output tsv
    # merge subtokens

    text = '#FORMAT=WebAnno TSV 3.2\n#T_SP=webanno.custom.Referent|entity|infstat\n#T_RL=webanno.custom.Coref|type|BT_webanno.custom.Referent\n'
    for sent in tsv:
        sent_out = []

        tok_num = 1
        for i, line in enumerate(sent):
            # remove [CLS]
            if line[2] == '[CLS]':
                continue
            # remove [SEP]
            if line[2] == '[SEP]':
                continue
            if line[2].startswith('##'):
                cur_subtok = line[2].replace('#', '')
                sent_out[-1][2] += cur_subtok
                continue
            # line_text = '\t'.join(line)
            line[0] = line[0].split('-')[0] + '-' + str(tok_num)
            tok_num += 1
            sent_out.append(line)

        text += '\n'.join(['\t'.join(x) for x in sent_out]) + '\n'

    with io.open('../out/preds/tsv'+os.sep+f_name+'.tsv', 'w', encoding='utf-8') as f:
        f.write(text)

print('Done!')
