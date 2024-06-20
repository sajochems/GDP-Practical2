import scipy

import mathutils

from scipy.sparse import coo_array, eye_array, sparray, diags

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

    num_verts = len(mesh.verts)
    rows, cols = [], []
    for edge in mesh.edges:
        i, j = edge.verts[0].index, edge.verts[1].index
        rows.extend([i, j])
        cols.extend([j, i])
    data = np.ones(len(rows), dtype=np.float64)
    return scipy.sparse.coo_matrix((data, (rows, cols)), shape=(num_verts, num_verts))


# !!! This function will be used for automatic grading, don't edit the signature !!!
def build_combinatorial_laplacian(mesh: bmesh.types.BMesh) -> scipy.sparse.sparray:
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

    A = adjacency_matrix(mesh)
    num_verts = A.shape[0]
    degrees = np.array(A.sum(axis=1)).flatten()
    # D = scipy.sparse.diags(degrees, format='coo')
    D_inv = scipy.sparse.diags(1.0 / degrees, format='coo')
    I = scipy.sparse.identity(num_verts, format='coo')
    L = I - D_inv @ A
    return L


def laplace_deform(mesh: bmesh.types.BMesh, tau: float, it: int = 1) -> np.ndarray:
    return iterative_implicit_laplace_smooth(mesh, tau, it)



def constrained_implicit_laplace_deform(mesh: bmesh.types.BMesh, selected_face_indices: list[int], tau: float, it: int) -> np.ndarray:

    # Convert mesh vertices to numpy array
    X = numpy_verts(mesh)

    # Perform smoothing operations
    result = mesh.copy()
    X_transformed = X.copy()
    for _ in range(it):
        M, Mv = build_mass_matrices(result)

        #G = build_gradient_matrix(result)

        S = other_cotangent(result)
        
        Xb = X_transformed.copy()
        X_transformed = implicit_laplace_smooth(Xb, M, S, tau)

    selected_verts = set()
    for i, face in enumerate(mesh.faces):
        if (i in selected_face_indices):
            for vert in face.verts:
                selected_verts.add(vert.index)
    selected_verts = list(selected_verts)

    X_final = X.copy()
    for i in selected_verts:
        X_final[i] = X_transformed[i]

    result = set_verts(mesh, X_final)

    return result


def constrained_explicit_laplace_deform(mesh: bmesh.types.BMesh, selected_face_indices: list[int], tau: float, it: int) -> bmesh.types.BMesh:

    X = numpy_verts(mesh)

    L = build_combinatorial_laplacian(mesh)

    X_transformed = X.copy()
    for _ in range(it):
        for i in range(3):
            X_transformed[:, i] = X_transformed[:, i] - tau * L @ X_transformed[:, i]

    selected_verts = set()
    for i, face in enumerate(mesh.faces):
        if (i in selected_face_indices):
            for vert in face.verts:
                selected_verts.add(vert.index)
    selected_verts = list(selected_verts)

    X_final = X.copy()
    for i in selected_verts:
        X_final[i] = X_transformed[i]

    set_verts(mesh, X_final)

    return mesh


def implicit_laplace_smooth(x: np.ndarray, M: scipy.sparse.sparray, S: scipy.sparse.sparray, tau: float) -> np.ndarray:
    """
    Performs smoothing of a list of vertices given a combinatorial Laplace matrix and a weight Tau.

    Updates are computed using the laplacian matrix and then weighted by Tau before subtracting from the vertices.

        x = x - tau * L @ x

    :param vertices: Vertices to apply offsets to as an Nx3 numpy array.
    :param L: The NxN sparse laplacian matrix
    :param tau: Update weight, tau=0 leaves the vertices unchanged, and tau=1 applies the full update.
    :return: The new positions of the vertices as an Nx3 numpy array.
    """

    #TODO

    # L = np.linalg.inv(M) @ S
    for i in range(3):  # Apply smoothing for x, y, z coordinates separately
        Mi = M.tocsr()
        Si = S.tocsr()
        A = Mi + tau * Si
        b = Mi @ x
        x = scipy.sparse.linalg.spsolve(A, b)

    return x


def explicit_laplace_smooth(
        vertices: np.ndarray,
        L: coo_array,
        tau: float,
) -> np.ndarray:
    """
    Performs smoothing of a list of vertices given a combinatorial Laplace matrix and a weight Tau.

    Updates are computed using the laplacian matrix and then weighted by Tau before subtracting from the vertices.

        x = x - tau * L @ x

    :param vertices: Vertices to apply offsets to as an Nx3 numpy array.
    :param L: The NxN sparse laplacian matrix
    :param tau: Update weight, tau=0 leaves the vertices unchanged, and tau=1 applies the full update.
    :return: The new positions of the vertices as an Nx3 numpy array.
    """
    for i in range(3):  # Apply smoothing for x, y, z coordinates separately
        x = vertices[:, i]
        vertices[:, i] = x - tau * L @ x
    return vertices



def iterative_explicit_laplace_smooth(
        mesh: bmesh.types.BMesh,
        tau: float,
        it: int
) -> bmesh.types.BMesh:
    """
    Performs smoothing of a given mesh using the iterative explicit Laplace smoothing.

    First, we define the coordinate vectors and the combinatorial Laplace matrix as numpy arrays.
    Then, we apply the smoothing operation as many times as iterations.
    We weight the updating vector in each iteration by tau.

    :param mesh: Mesh to smooth.
    :param tau: Update weight.
    :param iterations: Number of smoothing iterations to perform.
    :return: A mesh with the updated coordinates after smoothing.
    """

    # Get coordinate vectors as numpy arrays
    X = numpy_verts(mesh)

    # Compute combinatorial Laplace matrix
    L = build_combinatorial_laplacian(mesh)

    # Perform smoothing operations
    for _ in range(it):
        X = explicit_laplace_smooth(X, L, tau)

    # Write smoothed vertices back to output mesh
    set_verts(mesh, X)

    return mesh

def iterative_implicit_laplace_smooth(
        mesh: bmesh.types.BMesh,
        tau: float,
        iterations: int
) -> bmesh.types.BMesh:
    """
    Performs smoothing of a given mesh using the iterative implicit Laplace smoothing.

    First, we define the coordinate vectors and the combinatorial Laplace matrix as numpy arrays.
    Then, we apply the smoothing operation as many times as iterations.
    We weight the updating vector in each iteration by tau.

    :param mesh: Mesh to smooth.
    :param tau: Update weight.
    :param iterations: Number of smoothing iterations to perform.
    :return: A mesh with the updated coordinates after smoothing.
    """

    # Get coordinate vectors as numpy arrays
    X = numpy_verts(mesh)

    # Perform smoothing operations
    result = mesh.copy()
    for _ in range(iterations):
        M, Mv = build_mass_matrices(mesh)

        #G = build_gradient_matrix(mesh)

        S = other_cotangent(mesh)
        
        Xb = X.copy()
        X = implicit_laplace_smooth(Xb, M, S, tau)
        result = set_verts(mesh, X)

    return result

def cotangent_weight(v1, v2, v3):
    """
    Compute the cotangent weight for edge v1-v2 with the opposite vertex v3.
    """
    u = v1 - v2
    v = v3 - v2
    cos_theta = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    sin_theta = np.sqrt(1 - cos_theta**2)
    return cos_theta / sin_theta

def other_cotangent(mesh: bmesh.types.BMesh):
    num_verts = len(mesh.verts)
    row = []
    col = []
    data = []

    for face in mesh.faces:
        verts = [vert for vert in face.verts]
        indices = [vert.index for vert in face.verts]
        for i in range(3):
            v1, v2, v3 = verts[i], verts[(i + 1) % 3], verts[(i + 2) % 3]
            idx1, idx2 = indices[i], indices[(i + 1) % 3]
            weight = cotangent_weight(np.array(v1.co), np.array(v2.co), np.array(v3.co))
            row.append(idx1)
            col.append(idx2)
            data.append(weight)
            row.append(idx2)
            col.append(idx1)
            data.append(weight)

    # Convert the list to a sparse matrix
    L = coo_array((data, (row, col)), shape=(num_verts, num_verts))

    # Degree matrix (diagonal)
    D = coo_array((L.sum(axis=1).flatten(), (np.arange(num_verts), np.arange(num_verts))), shape=(num_verts, num_verts))

    # Laplacian matrix
    S = D - L

    return S
