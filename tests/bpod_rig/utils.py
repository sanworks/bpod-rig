
from bpod_rig.utils import get_func_params

def func(a, b, c=None, d='default'): ...
def func2(e, f, g=1, h='default'): ...

class TestGetFuncParams:
    def test_single_func(self):
        result = get_func_params(func)
        assert 'a' in result['required']
        assert 'b' in result['required']
        assert 'c' in result
        assert 'd' in result
        assert result['c'] is None
        assert result['d'] == 'default'

    def test_multiple_funcs(self):
        result = get_func_params(func, func2)
        assert 'a' in result['required']
        assert 'b' in result['required']
        assert 'c' in result
        assert 'd' in result
        assert result['c'] is None
        assert result['d'] == 'default'

        assert 'e' in result['required']
        assert 'f' in result['required']
        assert 'g' in result
        assert 'h' in result
        assert result['g'] == 1
        assert result['h'] == 'default'
