import pytest
from savman.vbackup import Backup

@pytest.fixture
def backup(filedir, file1, file2):    
    bak = Backup()
    bak.build(str(filedir))
    return bak

@pytest.fixture
def saved_backup(backup, tmpdir, bakfile):
    backup.save(bakfile)
    bak = Backup(bakfile)
    return bak

@pytest.fixture
def changed_backup(saved_backup, filedir, bakfile, file1):    
    bak = saved_backup
    file1.write('test1plus')
    bak.build(str(filedir))
    bak.save(bakfile)
    bak = Backup(bakfile)
    return bak

@pytest.fixture
def trimmed_backup(changed_backup, bakfile):    
    bak = changed_backup
    bak.vertrim(1)
    bak = Backup(bakfile)
    return bak

@pytest.fixture
def bakfile(tmpdir):
    file = tmpdir.join('test.vbak')
    return str(file)

@pytest.fixture
def file1(filedir):
    f1 = filedir.join('file1.txt')
    f1.write('test1');
    return f1

@pytest.fixture  
def file2(filedir):
    f2 = filedir.join('file2.txt')
    f2.write('test2');
    return f2

@pytest.fixture 
def filedir(tmpdir):
    return tmpdir.mkdir('files')


def test_build(backup, file1, file2, filedir):
    assert 'file1.txt' in backup.curver.files
    assert 'file2.txt' in backup.curver.files
    assert backup.curver.size == 10
    assert backup.curver.sizedelta == 10

def test_build_include(file1, file2, filedir):
    bak = Backup()
    bak.build(str(filedir), include=['file1.*'])
    assert 'file1.txt' in bak.curver.files
    assert 'file2.txt' not in bak.curver.files

def test_build_exclude(file1, file2, filedir):
    bak = Backup()
    bak.build(str(filedir), exclude=['*1.txt'])
    assert 'file1.txt' not in bak.curver.files
    assert 'file2.txt' in bak.curver.files

def test_save_load(backup, saved_backup):
    bak = saved_backup
    assert 'file1.txt' in bak.lastver.files
    assert 'file2.txt' in bak.lastver.files
    assert bak.src == backup.src

def test_change(saved_backup, changed_backup, file1):
    bak = changed_backup
    assert bak.lastver.files['file1.txt'].location == bak.lastver.id
    assert bak.lastver.files['file2.txt'].location == saved_backup.lastver.id
    assert bak.lastver.sizedelta == 9
    assert bak.lastver.size == 14

def test_trim(trimmed_backup):
    bak = trimmed_backup
    assert len(bak.versions) == 1
    assert bak.lastver.files['file2.txt'].location == bak.lastver.id
    assert bak.lastver.size == bak.lastver.sizedelta

def test_restore(changed_backup, tmpdir):
    bak = changed_backup
    f1 = tmpdir.join('file1.txt')
    bak.restore(str(tmpdir))
    assert f1.read() == 'test1plus'
    assert tmpdir.join('file2.txt').isfile()

def test_restorenum(changed_backup, tmpdir):
    bak = changed_backup
    f1 = tmpdir.join('file1.txt')
    bak.restorenum(1, str(tmpdir))
    assert f1.read() == 'test1'



