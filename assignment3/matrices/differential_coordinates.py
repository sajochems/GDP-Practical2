import bmesh
import numpy
import numpy as np
import scipy
from scipy.sparse import coo_array, sparray


# !!! This function will be used for automatic grading, don't edit the signature !!!
def triangle_gradient(triangle: bmesh.types.BMFace) -> np.ndarray:
    """
    Computes the local gradient of a triangular face.

    The local gradient $g$ is a 3x3 matrix where each column is the cross product of the triangle's normal
    with the vector representing one of its three edges, divided by half of its area, so:

        g = [(N \cross e_1) (N \cross e_2) (N \cross e_3)] / 2A

    Where $N$ is the triangle's normal, $e_i$ is the ith edge of the triangle, and A is the triangle's area.

    :param triangle: Triangular face to find the local gradient of.
    :return: A 3x3 gradient matrix.
    """

    assert len(triangle.verts) == 3
    normal = np.array(triangle.normal)
    local_gradient = numpy.zeros([3, 3])

    area = triangle.calc_area()
    verts = [v.co for v in triangle.verts]
    v0, v1, v2 = np.array(verts[0]), np.array(verts[1]), np.array(verts[2])

    e0 = np.array(v2 - v1)
    e1 = np.array(v0 - v2)
    e2 = np.array(v1 - v0)

    edges = [e0, e1, e2]

    local_gradient[0] = np.cross(normal, edges[0]) / (2. * area)
    local_gradient[1] = np.cross(normal, edges[1]) / (2. * area)
    local_gradient[2] = np.cross(normal, edges[2]) / (2. * area)

    # TODO: Find the local gradient for this triangle.
    return local_gradient


# !!! This function will be used for automatic grading, don't edit the signature !!!
def build_gradient_matrix(mesh: bmesh.types.BMesh) -> sparray:
    """
    Computes the gradient matrix $G$ for a triangular mesh.

    The local gradient of each triangle in the mesh appears in the overall mesh gradient matrix,
    but its rows are distributed along the columns according to the index of the vertex they are associated with.
    For more information, see the slides.

    :param mesh: Triangular mesh to find the gradient matrix of.
    :return: A 3MxN gradient matrix,
             where M and N are the number of triangles and number of vertices in the mesh, respectively.
    """
    num_faces, num_verts = len(mesh.faces), len(mesh.verts)

    row = []
    col = []
    data = []

    for i, face in enumerate(mesh.faces):
        gradient_matrix = triangle_gradient(face)

        for j, vert in enumerate(face.verts):
            for k in range(3):
                row.append(3 * i + k)
                col.append(vert.index)
                data.append(gradient_matrix[k, j])

    # TODO: construct the sparse gradient matrix for the mesh
    return coo_array((data, (row, col)), shape=(num_faces * 3, num_verts))


# !!! This function will be used for automatic grading, don't edit the signature !!!
def build_mass_matrices(mesh: bmesh.types.BMesh) -> tuple[sparray, sparray]:
    """
    Computes the mass matrices $M$ and $Mv$ for a triangular mesh.

    In both mass matrices, elements only appear along the diagonal, all other elements are zero:

        $M_ii$ is the sum of the area of each triangle connected to vertex $i$,

        $Mv_(3i+l)(3i+l)$ is the area of triangle $i$, where $l$ is the index (0, 1, 2) of each vertex of the triangle.

    For more information, see the slides.

    :param mesh: Triangular mesh to find the mass matrices of.
    :return: A tuple containing the NxN sparse matrix $M$ and the 3Mx3M sparse matrix $Mv$,
             where M and N are the number of triangles and number of vertices in the mesh, respectively.
    """
    num_face, num_verts = len(mesh.faces), len(mesh.verts)
    # TODO: construct the mass matrices M and Mv for the mesh

    M_diag = np.zeros(num_verts)
    Mv_diag = np.zeros(3 * num_face)

    for i, face in enumerate(mesh.faces):
        area = face.calc_area()

        for j, vert in enumerate(face.verts):
            M_diag[vert.index] += area

            Mv_diag[3 * i + j] = area

    M_diag[M_diag != 0] /= 3.0
    M = scipy.sparse.diags(M_diag)
    Mv = scipy.sparse.diags(Mv_diag)

    return M, Mv


# !!! This function will be used for automatic grading, don't edit the signature !!!
def build_cotangent_matrix(G: sparray, Mv: sparray) -> sparray:
    """
    Computes the cotangent matrix $S$ from the gradient and mass matrices.

    :param G: A 3MxN gradient matrix.
    :param Mv: A 3Mx3M mass matrix.
    :return: A NxN cotangent matrix.
    """
    # TODO: find the cotangent matrix S based on G and Mv
    S = G.T @ Mv @ G

    return S
