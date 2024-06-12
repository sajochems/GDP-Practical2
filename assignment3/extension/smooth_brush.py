import scipy

import mathutils

from assignment3.matrices.util import *
from assignment3.matrices.differential_coordinates import *


def numpy_verts(mesh: bmesh.types.BMesh) -> np.ndarray:
    """
    Extracts a numpy array of (x, y, z) vertices from a blender mesh

    :param mesh: The BMesh to extract the vertices of.
    :return: A numpy array of shape [n, 3], where array[i, :] is the x, y, z coordinate of vertex i.
    """
    data = bpy.data.meshes.new('tmp')
    mesh.to_mesh(data)
    # Explained here:
    # https://blog.michelanders.nl/2016/02/copying-vertices-to-numpy-arrays-in_4.html
    vertices = np.zeros(len(mesh.verts) * 3, dtype=np.float64)
    data.vertices.foreach_get('co', vertices)
    return vertices.reshape([len(mesh.verts), 3])


def set_verts(mesh: bmesh.types.BMesh, verts: np.ndarray) -> bmesh.types.BMesh:
    data = bpy.data.meshes.new('tmp1')  # temp Blender Mesh to perform fast setting
    mesh.to_mesh(data)
    data.vertices.foreach_set('co', verts.ravel())
    mesh.clear()
    mesh.from_mesh(data)
    return mesh


# HINT: This is a helper method which you can change (for example, if you want to try different sparse formats)
def adjacency_matrix(mesh: bmesh.types.BMesh) -> scipy.sparse.coo_matrix:
    """
    Computes the adjacency matrix of a mesh.

    Computes the adjacency matrix of the given mesh.
    Uses a sparse data structure to represent the matrix,
    which is more efficient for operations like matrix multiplication.

    :param mesh: Mesh to compute the adjacency matrix of.
    :return: A sparse matrix representing the mesh adjacency matrix.
    """
    # HINT: Iterating over mesh.edges is significantly faster than iterating over mesh.verts and getting neighbors!
    #       Building a sparse matrix from a set of I, J, V triplets is also faster than adding elements sequentially.
    # TODO: Create a sparse adjacency matrix using one of the types from scipy.sparse
    num_verts = len(mesh.verts)
    rows, cols = [], []
    for edge in mesh.edges:
        i, j = edge.verts[0].index, edge.verts[1].index
        rows.extend([i, j])
        cols.extend([j, i])
    data = np.ones(len(rows), dtype=np.float64)
    return scipy.sparse.coo_matrix((data, (rows, cols)), shape=(num_verts, num_verts))


# !!! This function will be used for automatic grading, don't edit the signature !!!
def build_combinatorial_laplacian(mesh: bmesh.types.BMesh) -> sparray:
    """
    Computes the normalized combinatorial Laplacian the given mesh.

    First, the adjacency matrix is computed efficiently using the edge_matrix function.
    Then the normalized Laplacian is calculated using the sparse operations: L = I-A/D
    where I is the identity and D the degree matrix.
    The resulting mesh should have the following properties:
        - L_ii = 1
        - L_ij = - 1 / deg_i (if an edge exists between i and j)
        - L_ij = 0 (if such an edge does not exist)
    Where deg_i is the degree of node i (its number of edges).

    :param mesh: Mesh to compute the normalized combinatorial Laplacian matrix of.
    :return: A sparse array representing the mesh Laplacian matrix.
    """
    # TODO: Build the combinatorial laplacian matrix
    A = adjacency_matrix(mesh)
    num_verts = A.shape[0]
    degrees = np.array(A.sum(axis=1)).flatten()
    D = scipy.sparse.diags(degrees, format='coo')
    D_inv = scipy.sparse.diags(1.0 / degrees, format='coo')
    I = scipy.sparse.identity(num_verts, format='coo')
    L = I - D_inv @ A
    return L


# TODO: Implement the function below
def laplace_smooth():
    pass


# TODO Computing the mesh that best matches the modified Laplace coordinates
def laplace_deform():
    pass