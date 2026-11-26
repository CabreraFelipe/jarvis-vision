"""Run only with explicit --run, using synthetic data and an installed local model."""
import argparse,sys,time,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from semantic_memory import retrieve,MODEL
from memory import relevant

NOTES=[
 (1,'Tengo una gata de color blanco llamada Nube.'),
 (2,'Prefiero escuchar música electrónica de estilo house.'),
 (3,'Estoy preparando una carrera de diez kilómetros.'),
 (4,'Mi alimento favorito es la pasta con salsa de tomate.'),
 (5,'Estudio anatomía patológica en la facultad.'),
 (6,'Trabajo desarrollando aplicaciones con Python.'),
 (7,'Disfruto visitar playas durante las vacaciones.'),
 (8,'Prefiero respuestas breves y concretas.'),
]
CASES=[
 ('¿Cómo se llama mi mascota felina?',1),
 ('¿Qué género de canciones disfruto?',2),
 ('¿Para qué competencia deportiva me preparo?',3),
 ('¿Qué plato me gusta comer?',4),
 ('¿Qué materia médica estoy cursando?',5),
 ('¿A qué me dedico profesionalmente?',6),
 ('¿Dónde me gusta descansar en verano?',7),
 ('¿Cómo me gusta que me contestes?',8),
 ('¿Cuál es la capital de Islandia?',None),
 ('¿Cuánto mide el monte Everest?',None),
 ('¿Qué es una reacción nuclear?',None),
 ('¿Quién escribió Don Quijote?',None),
]
def run(retriever=retrieve,clock=time.perf_counter):
    results=[]
    for question,expected in CASES:
        start=clock()
        matches=retriever(NOTES,question)
        elapsed=clock()-start
        ids=[i for i,_ in matches]
        lexical=[i for i,_ in relevant(NOTES,question)]
        results.append((question,expected,ids,lexical,elapsed))
    return results

def report(results):
    positive=[r for r in results if r[1] is not None]
    negative=[r for r in results if r[1] is None]
    for question,expected,ids,lexical,elapsed in results:
        print(f'{question} | esperado={expected} sem={ids} literal={lexical} | {elapsed:.2f}s')
    print('Top 1:',sum(bool(r[2]) and r[2][0]==r[1] for r in positive),'/',len(positive))
    print('Recuperado:',sum(r[1] in r[2] for r in positive),'/',len(positive))
    print('Falsos positivos (sin recuerdo esperado):',sum(bool(r[2]) for r in negative),'/',len(negative))
    print('Latencia mediana:',round(statistics.median(r[4] for r in results),2),'s')
    print('Banco pequeño exploratorio; no garantiza relevancia general.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='Autorizar prueba con Ollama local y notas ficticias')
    args=parser.parse_args()
    if not args.run:parser.error('Se requiere --run; no se descargan modelos')
    print('Modelo:',MODEL)
    report(run())
