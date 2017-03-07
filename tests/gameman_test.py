import pytest
from savman import gameman

@pytest.fixture
def dir1(tmpdir):
    return tmpdir.mkdir('dir1')

@pytest.fixture
def dir2(tmpdir):
    return tmpdir.mkdir('dir2')

@pytest.fixture
def customfile(tmpdir, dir1, dir2):
    file = tmpdir.join('custom.txt')
    custom = '''
---
name: My Game
directory: {}
include:
- folder1/*   # Include all files from folder
exclude:
- '*.png'
---
name: My Game 2
directory: {}
'''.format(str(dir1), str(dir2))
    file.write(custom)
    return file



def test_load_custom(customfile, dir1, dir2):
    gman = gameman.GameMan('DUMMY')
    gman.load_custom(str(customfile))
    assert 'MyGame' in gman.games
    assert 'MyGame2' in gman.games
    game1 = gman.games['MyGame']
    game2 = gman.games['MyGame2']
    assert game1.name == 'My Game'
    assert game2.name == 'My Game 2'
    assert game1.locations[0].path == str(dir1)
    assert game2.locations[0].path == str(dir2)
    assert 'folder1/*' in game1.locations[0].include
    assert '*.png' in game1.locations[0].exclude  