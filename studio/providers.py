import os
import json
import urllib.request
from .core import replay_provider

def provider(mode):
    if mode=='replay':return replay_provider
    if mode=='bedrock':
        model=os.getenv('BEDROCK_MODEL_ID')
        if not model:raise ValueError('Set BEDROCK_MODEL_ID before using Bedrock.')
        try:import boto3
        except ImportError:raise ValueError('Install boto3 to enable Bedrock.')
        from botocore.config import Config
        client=boto3.client('bedrock-runtime',region_name=os.getenv('AWS_REGION','us-east-1'),config=Config(connect_timeout=5,read_timeout=25,retries={'max_attempts':0}))
        def invoke(text,row,prompt):
            r=client.converse(modelId=model,messages=[{'role':'user','content':[{'text':text}]}],inferenceConfig={'maxTokens':512,'temperature':0})
            return {'text':''.join(c.get('text','') for c in r['output']['message']['content']),'usage':{'input_tokens':r['usage']['inputTokens'],'output_tokens':r['usage']['outputTokens']}}
        return invoke
    if mode=='http':
        base=os.getenv('LLM_BASE_URL','').rstrip('/');model=os.getenv('LLM_MODEL','');key=os.getenv('LLM_API_KEY','')
        if not base.startswith(('http://','https://')) or not model:raise ValueError('Set LLM_BASE_URL and LLM_MODEL for an OpenAI-compatible endpoint.')
        def invoke(text,row,prompt):
            payload={'model':model,'messages':[{'role':'user','content':text}],'temperature':0,'max_tokens':512}
            headers={'Content-Type':'application/json'}
            if key:headers['Authorization']='Bearer '+key
            req=urllib.request.Request(base+'/chat/completions',data=json.dumps(payload).encode(),headers=headers)
            try:
                with urllib.request.urlopen(req,timeout=25) as response: raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError('Provider response exceeds 2 MB.')
                data=json.loads(raw)
            except Exception:raise ValueError('Provider request failed. Check the endpoint, credentials, and model.')
            usage=data.get('usage');tokens={'input_tokens':usage['prompt_tokens'],'output_tokens':usage['completion_tokens']} if usage and 'prompt_tokens' in usage and 'completion_tokens' in usage else None
            return {'text':data['choices'][0]['message']['content'],'usage':tokens}
        return invoke
    raise ValueError('Provider must be replay, bedrock, or http.')
