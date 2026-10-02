import json
import os
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Request,BackgroundTasks
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from .core import check_dataset,evaluate
from .providers import provider
from . import store
DB=os.getenv('EVAL_DB','data/evals.sqlite');STATIC=Path(__file__).resolve().parent.parent/'static';LOCK=threading.Lock()
@asynccontextmanager
async def lifespan(app):
    with store.db(DB) as conn:
        conn.execute("UPDATE runs SET status='failed',payload=? WHERE status IN ('queued','running')",(json.dumps({'error':'Server restarted during batch execution.'}),))
    yield
app=FastAPI(title='LLM Eval Studio',lifespan=lifespan)
async def body(request):
    raw=bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw)>1_000_000:raise HTTPException(413,'Request exceeds 1 MB.')
    data=json.loads(raw)
    if not isinstance(data,dict):raise ValueError('Request must be an object.')
    return data
@app.exception_handler(ValueError)
async def invalid(request,error):return JSONResponse({'detail':str(error)},status_code=400)
@app.get('/api/artifacts')
def artifacts():return store.artifacts(DB)
@app.post('/api/datasets')
async def dataset(request:Request):
    data=await body(request);rows=check_dataset(data.get('cases'));name=data.get('name')
    if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('Name must be 1–100 characters.')
    return store.save(DB,'dataset',name.strip(),rows)
@app.post('/api/prompts')
async def prompt(request:Request):
    data=await body(request);name=data.get('name');template=data.get('template')
    if not isinstance(name,str) or not 1<=len(name.strip())<=100 or not isinstance(template,str) or not 1<=len(template)<=10000 or '{input}' not in template:raise ValueError('Provide a name and a template containing {input}.')
    return store.save(DB,'prompt',name.strip(),{'template':template})
@app.get('/api/runs')
def runs():return store.runs(DB)
@app.get('/api/runs/{id}')
def run(id:int):
    saved=store.run(DB,id)
    if not saved:raise HTTPException(404,'Run not found.')
    return saved

def execute(path,id,dataset,prompts,mode,input_price,output_price,invoke):
    try:
        store.update_run(path,id,'running',{'provider':mode,'dataset':dataset,'results':[]})
        results=[evaluate(dataset['payload'],{'id':p['id'],'name':p['name'],'version':p['version'],'template':p['payload']['template']},invoke,input_price,output_price) for p in prompts]
        store.update_run(path,id,'completed',{'provider':mode,'dataset':dataset,'results':results,'input_price_per_million':input_price,'output_price_per_million':output_price})
    except Exception as error:store.update_run(path,id,'failed',{'error':str(error)[:300]})
    finally:LOCK.release()
@app.post('/api/runs')
async def start(request:Request,tasks:BackgroundTasks):
    data=await body(request);dataset=store.get(DB,data.get('dataset_id'));ids=data.get('prompt_ids')
    if not dataset or dataset['kind']!='dataset':raise ValueError('Select a saved dataset.')
    if not isinstance(ids,list) or not 1<=len(ids)<=3 or any(type(id) is not int for id in ids) or len(set(ids))!=len(ids):raise ValueError('Select 1–3 distinct prompt versions.')
    prompts=[store.get(DB,id) for id in ids]
    if any(not p or p['kind']!='prompt' for p in prompts):raise ValueError('Prompt not found.')
    mode=data.get('provider','replay');invoke=provider(mode)
    prices=[data.get('input_price',0),data.get('output_price',0)]
    import math
    if any(type(p) not in (int,float) or not math.isfinite(p) or p<0 for p in prices):raise ValueError('Prices must be finite nonnegative numbers.')
    if not LOCK.acquire(blocking=False):raise HTTPException(429,'A batch is already running.')
    try:id=store.create_run(DB,{'provider':mode,'dataset_id':dataset['id'],'prompt_ids':ids})
    except Exception:LOCK.release();raise
    tasks.add_task(execute,DB,id,dataset,prompts,mode,*prices,invoke)
    return {'id':id,'status':'queued'}
@app.get('/')
def index():return FileResponse(STATIC/'index.html')
app.mount('/static',StaticFiles(directory=STATIC),name='static')
