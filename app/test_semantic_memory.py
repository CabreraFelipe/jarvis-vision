import io,json,unittest
from unittest.mock import Mock,patch
from semantic_memory import retrieve,rank_vectors,resolve_notes,MODEL,NoRedirect,BASE
from threading import Event

class SemanticTests(unittest.TestCase):
    def test_rank_and_threshold(self):
        rows=[(1,'nota antigua'),(2,'nota pertinente'),(3,'otra')]
        self.assertEqual(rank_vectors(rows,[[1,0],[0,1],[0.95,0.05],[-1,0]]),[(2,'nota pertinente')])
    def test_invalid_vectors(self):
        for vectors in ([[1,0]],[[1,0],[1]],[[1,0],[float('nan'),1]],[[1,0],[0,0]],[[1,0],[True,1]]):
            with self.subTest(vectors=vectors),self.assertRaises(ValueError):
                rank_vectors([(1,'nota')],vectors)
    def test_batch_local_no_proxy(self):
        opener=Mock()
        opener.open.side_effect=[io.BytesIO(json.dumps({'models':[{'name':MODEL}]}).encode()),
            io.BytesIO(b'{"embeddings":[[1,0],[1,0]]}')]
        with patch('semantic_memory.urllib.request.build_opener',return_value=opener) as build:
            self.assertEqual(retrieve([(1,'nota')],'pregunta'),[(1,'nota')])
        self.assertEqual(build.call_args.args[0].proxies,{})
        self.assertIsInstance(build.call_args.args[1],NoRedirect)
        first,second=[c.args[0] for c in opener.open.call_args_list]
        self.assertEqual(first.full_url,BASE+'/api/tags')
        self.assertEqual(second.full_url,BASE+'/api/embed')
        self.assertEqual(json.loads(second.data)['input'],['pregunta','nota'])
    def test_missing_model_does_not_send_notes(self):
        opener=Mock();opener.open.return_value=io.BytesIO(b'{"models":[]}')
        with patch('semantic_memory.urllib.request.build_opener',return_value=opener):
            with self.assertRaises(ValueError):retrieve([(1,'nota privada')],'pregunta')
        opener.open.assert_called_once()
    def test_empty_never_contacts_service(self):
        with patch('semantic_memory.urllib.request.build_opener') as build:
            self.assertEqual(retrieve([],'pregunta'),[])
            self.assertEqual(retrieve([(1,'nota')],' '),[])
            build.assert_not_called()
    def test_hybrid_retains_exact_and_deduplicates(self):
        with patch('semantic_memory.retrieve',return_value=[(1,'igual'),(2,'concepto')]):
            self.assertEqual(resolve_notes(('igual',),[(1,'igual'),(2,'concepto')],'pregunta',Event()),(('igual','concepto'),'Semántica local'))
    def test_fallback_and_no_consent(self):
        with patch('semantic_memory.retrieve',side_effect=OSError) as engine:
            self.assertEqual(resolve_notes(('nota',),[],'pregunta',Event()),(('nota',),''))
            engine.assert_not_called()
            self.assertEqual(resolve_notes(('nota',),[(1,'nota')],'pregunta',Event())[0],('nota',))
    def test_cancelled_never_calls_engine(self):
        event=Event();event.set()
        with patch('semantic_memory.retrieve') as engine:
            self.assertEqual(resolve_notes(('nota',),[(1,'nota')],'pregunta',event),((),'Cancelada'))
            engine.assert_not_called()
    def test_cancel_during_retrieval_discards_notes(self):
        event=Event()
        def stop(*args,**kwargs):
            event.set()
            return [(1,'nota')]
        with patch('semantic_memory.retrieve',side_effect=stop):
            self.assertEqual(resolve_notes((),[(1,'nota')],'pregunta',event),((),'Cancelada'))
    def test_cancel_before_embedding_does_not_send_notes(self):
        event=Event();opener=Mock()
        def tags(*args,**kwargs):
            event.set()
            return io.BytesIO(json.dumps({'models':[{'name':MODEL}]}).encode())
        opener.open.side_effect=tags
        with patch('semantic_memory.urllib.request.build_opener',return_value=opener):
            self.assertEqual(retrieve([(1,'nota privada')],'pregunta',cancelled=event),[])
        opener.open.assert_called_once()
    def test_context_budget_with_many_matches(self):
        from memory import MAX_CONTEXT
        matches=[(i,str(i)+'x'*290) for i in range(30)]
        with patch('semantic_memory.retrieve',return_value=matches):
            notes,_=resolve_notes(('coincidencia literal',),matches,'pregunta',Event())
        self.assertEqual(notes[0],'coincidencia literal')
        self.assertLessEqual(sum(map(len,notes)),MAX_CONTEXT)
    def test_redirect_refused(self):
        with self.assertRaises(ValueError):NoRedirect().redirect_request()

if __name__=='__main__':unittest.main()
