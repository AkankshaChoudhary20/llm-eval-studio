import time
import math

def check_dataset(rows):
    if not isinstance(rows,list) or not 1<=len(rows)<=50: raise ValueError('Dataset must contain 1–50 cases.')
    ids=set()
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id'] or row['id'] in ids: raise ValueError('Cases need unique nonempty string IDs.')
        ids.add(row['id'])
        if not isinstance(row.get('input'),str) or len(row['input'])>10000: raise ValueError('Each case needs an input string of at most 10,000 characters.')
        if 'expected' not in row and not row.get('contains'): raise ValueError('Each case needs expected text or contains assertions.')
        if 'expected' in row and not isinstance(row['expected'],str): raise ValueError('Expected output must be text.')
        if 'contains' in row and (not isinstance(row['contains'],list) or not row['contains'] or any(not isinstance(x,str) or not x for x in row['contains'])): raise ValueError('contains must be a nonempty array of nonempty strings.')
        if 'outputs' in row and (not isinstance(row['outputs'],dict) or any(not isinstance(x,str) for x in row['outputs'].values())): raise ValueError('Replay outputs must map prompt names to text.')
    return rows

def score(row,output):
    checks=[]
    if 'expected' in row: checks.append({'name':'exact_match','passed':output.strip()==row['expected'].strip()})
    for phrase in row.get('contains',[]): checks.append({'name':'contains: '+phrase,'passed':phrase in output})
    return {'passed':all(c['passed'] for c in checks),'checks':checks}

def evaluate(rows,prompt,provider,input_price=0,output_price=0):
    check_dataset(rows)
    if not isinstance(prompt,dict) or not isinstance(prompt.get('name'),str) or not prompt['name'].strip() or not isinstance(prompt.get('template'),str):
        raise ValueError('Prompt needs a nonempty name and a text template.')
    for value in (input_price,output_price):
        if type(value) not in (float,int) or value < 0 or value > 1.7976931348623157e308 or not math.isfinite(value): raise ValueError('Token prices must be finite nonnegative numbers.')
    results=[]
    for row in rows:
        started=time.perf_counter()
        try:
            answer=provider(prompt['template'].replace('{input}',row['input']),row,prompt)
            text=answer['text']
            if not isinstance(text,str): raise ValueError('Provider returned a non-text output.')
            judged=score(row,text)
            usage=answer.get('usage')
            if usage is not None:
                if not isinstance(usage,dict) or any(type(usage.get(key)) is not int or usage[key] < 0 for key in ('input_tokens','output_tokens')):
                    raise ValueError('Provider usage must contain nonnegative integer token counts.')
            # Scale token counts first to avoid intermediate overflow or price underflow.
            cost=((usage['input_tokens']/1_000_000)*input_price+(usage['output_tokens']/1_000_000)*output_price) if usage else None
            if cost is not None and not math.isfinite(cost):
                raise ValueError('Estimated cost must be finite.')
            results.append({'id':row['id'],'output':text,**judged,'latency_ms':round((time.perf_counter()-started)*1000,2),'usage':usage,'estimated_cost_usd':cost,'error':None})
        except Exception as error:
            results.append({'id':row['id'],'output':'','passed':False,'checks':[],'latency_ms':round((time.perf_counter()-started)*1000,2),'usage':None,'estimated_cost_usd':None,'error':(str(error) or type(error).__name__)[:300]})
    latencies=sorted(r['latency_ms'] for r in results)
    return {'prompt':prompt,'cases':results,'pass_rate':sum(r['passed'] for r in results)/len(results),'error_count':sum(r['error'] is not None for r in results),'mean_latency_ms':sum(latencies)/len(latencies),'p95_latency_ms':latencies[max(0,math.ceil(.95*len(latencies))-1)],'estimated_cost_usd':sum(r['estimated_cost_usd'] for r in results) if all(r['estimated_cost_usd'] is not None for r in results) else None}

def replay_provider(text,row,prompt):
    outputs=row.get('outputs',{})
    if prompt['name'] not in outputs: raise ValueError('No recorded output for prompt '+prompt['name'])
    return {'text':outputs[prompt['name']]}

