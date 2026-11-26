import io,json,unittest
from unittest.mock import Mock,patch
from semantic_memory import retrieve,rank_vectors,MODEL,NoRedirect,BASE

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
    def test_redirect_refused(self):
        with self.assertRaises(ValueError):NoRedirect().redirect_request()

if __name__=='__main__':unittest.main()
