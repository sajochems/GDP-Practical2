import unittest
import numpy as np
from mathutils import Matrix, Vector
from scipy.sparse import csr_array

from .differential_coordinates import *
from data import primitives, meshes


class TestGradient(unittest.TestCase):
    # HINT: Add your own unit tests here
    pass


class TestMassMatrices(unittest.TestCase):
    # HINT: Add your own unit tests here
    pass


class TestCotangentMatrix(unittest.TestCase):
    G = csr_array(np.array([[1, 2], [3, 4]]))
    Mv = csr_array(np.array([[2, 0], [0, 2]]))

    S = np.array([[20, 28], [28, 40]])


    cotang = build_cotangent_matrix(G, Mv)
    print(cotang)
    print(S)
    assert True
