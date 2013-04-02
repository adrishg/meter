from parser import Parser
from scanner import Scanner

def test_1():
    p = Parser('tests/simple-cats.yaml')
    x = p.tokenize('uu uv!')
    assert ['uu', ' ', 'u', 'v', '!'] == x, x

def test_2():
    p = Parser('tests/simple-cats.yaml')
    x = p.parse('uu uv!')
    assert 'vsc' == x, x
    
def test_3():
    s = Scanner()
    input_string = 'naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa'
    scan_results = s.scan(input_string, known_only=True)

    assert len(scan_results['results']) == 1
    
    result = scan_results['results'][0]
    assert len(scan_results['results']) == 1
    assert result['scan'] == '=-===-===-===-=', result['scan']
