import os
import sys
import pickle
import numpy as np
from orphics.stats import FisherMatrix

def _get_header(file_):
    with open(file_) as filein:
        header = filein.readline()
        header = header.lstrip('#')
        header = header.rstrip('\n')
        header = header.replace(' ', '')
        header = header.split(',')
    return header

def load_fisher(file_):
    filename, file_extension = os.path.splitext(file_)

    if file_extension == '.txt':
        try:
            fisher_raw = np.loadtxt(file_, delimiter=',')
        except ValueError:
            fisher_raw = np.loadtxt(file_, delimiter=' ')

        params = _get_header(file_)
        fisher = FisherMatrix(fisher_raw, params)

    elif file_extension == '.pkl':
        try:
            with open(file_, 'rb') as pickle_file:
                fisher = pickle.load(pickle_file)
        except UnicodeDecodeError:
            with open(file_, 'rb') as pickle_file:
                fisher = pickle.load(pickle_file, encoding='latin1')

        fisher.params = fisher.columns.values.tolist()
    else:
        print(f"Filetype of extra fisher file {file_} not supported")
        sys.exit()
    assert fisher.params is not None
    assert type(fisher) is FisherMatrix
    return fisher

def test_load_fisher_smallfile():
    #requires the existence of load_fisher_test.txt with the contents (after stripping #>):
    #>#tau,H0
    #10,0
    #0,0

    params = ['tau', 'H0']
    fishervals = np.array([[10,0],[0,0]], dtype=float)

    fishermat = FisherMatrix(fishervals, params)
    
    try:
        testfishermat = load_fisher('userdata/testdata/load_fisher_test.txt')
    except OSError as e:
        print(e)
        print("You probably didn't create the file userdata/testdata/load_fisher_test.txt with the contents:")
        print("\n#tau,H0\n10,0\n0,0")
        print("\nTrying creating that and running this test again")
        sys.exit()

    try:
        assert fishermat.equals(testfishermat)
        print("Test load_fisher_smallfile passed")
    except AssertionError:
        print("Test load_fisher_smallfile failed: here is what was expected:")
        print(fishermat)
        print("Here is what was loaded:")
        print(testfishermat)

if __name__ == '__main__':
    test_load_fisher_smallfile()
