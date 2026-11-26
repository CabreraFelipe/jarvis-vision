"""Experimental local semantic ranking. No disk writes, model pulls or UI integration."""
import json
import math
import urllib.request

MODEL='bge-m3:latest'
BASE='http://127.0.0.1:11434'
MAX_NOTES=100
MAX_NOTE=300
MAX_QUESTION=4000
MAX_RESPONSE=8*1024*1024
MAX_DIM=4096
MIN_SCORE=0.65  # provisional; calibrate on Spanish examples before enabling

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Redirección no permitida')

def local_json(opener,path,payload=None):
    if path not in ('/api/tags','/api/embed'):
        raise ValueError('Ruta no autorizada')
    req=urllib.request.Request(BASE+path,
        data=None if payload is None else json.dumps(payload).encode('utf-8'),
        headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=15) as response:
        raw=response.read(MAX_RESPONSE+1)
    if len(raw)>MAX_RESPONSE: raise ValueError('Respuesta excesiva')
    return json.loads(raw)

def unit(vector):
    if not isinstance(vector,list) or not 1<=len(vector)<=MAX_DIM:
        raise ValueError('Vector inválido')
    if any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e6 for x in vector):
        raise ValueError('Vector inválido')
    length=math.sqrt(sum(x*x for x in vector))
    if not length: raise ValueError('Vector nulo')
    return [x/length for x in vector]

def rank_vectors(rows,vectors,min_score=MIN_SCORE):
    if len(vectors)!=len(rows)+1: raise ValueError('Cantidad de vectores inválida')
    query=unit(vectors[0])
    ranked=[]
    for (note_id,note),raw in zip(rows,vectors[1:]):
        v=unit(raw)
        if len(v)!=len(query): raise ValueError('Dimensiones inconsistentes')
        score=sum(a*b for a,b in zip(query,v))
        if score>=min_score: ranked.append((score,note_id,note))
    return [(i,note) for _,i,note in sorted(ranked,reverse=True)]

def retrieve(rows,question):
    """Call only after explicit consent, in worker. Raises on error; caller owns fallback."""
    if not isinstance(question,str) or len(question)>MAX_QUESTION:
        raise ValueError('Consulta fuera de límites')
    rows=list(rows)
    if not rows or not question.strip():return []
    if len(rows)>MAX_NOTES or any(type(i) is not int or not isinstance(t,str) or not 1<=len(t)<=MAX_NOTE for i,t in rows):
        raise ValueError('Notas fuera de límites')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    tags=local_json(opener,'/api/tags')
    if not any(isinstance(x,dict) and MODEL in (x.get('name'),x.get('model')) for x in tags['models']):
        raise ValueError('Modelo semántico local no instalado')
    result=local_json(opener,'/api/embed',{'model':MODEL,'input':[question]+[t for _,t in rows],'truncate':False})
    return rank_vectors(rows,result['embeddings'])
