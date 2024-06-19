import bmesh.ops
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
    # for _ in range(it):
        # bmesh.ops.smooth_laplacian_vert(mesh, verts=list(mesh.verts), lambda_factor=tau, use_x=True, use_y=True, use_z=True)
    return iterative_implicit_laplace_smooth(mesh, tau, it)


def constrained_laplace_deform(mesh: bmesh.types.BMesh, selected_face_indices: list[int], tau: float) -> np.ndarray:
    # Step 1: Mark the area to be deformed (vertices of selected faces)
    selected_verts = set()
    for face_idx in selected_face_indices:
        face = mesh.faces[face_idx]
        for vert in face.verts:
            selected_verts.add(vert.index)
    selected_verts = list(selected_verts)

    # Convert mesh vertices to numpy array
    verts = numpy_verts(mesh)

    # Step 2: Compute the Laplace coordinates
    L = build_combinatorial_laplacian(mesh)
    laplace_coords = L @ verts

    # Step 3: Deform the Laplace coordinates (for example, scale them)
    deformed_laplace_coords = laplace_coords.copy()
    deformed_laplace_coords[selected_verts] *= tau

    # Step 4: Compute the mesh that best matches the modified Laplace coordinates
    deformed_verts = scipy.sparse.linalg.spsolve(L, deformed_laplace_coords)

    # Update the mesh vertices with the deformed vertices
    deformed_mesh = set_verts(mesh, deformed_verts)

    return deformed_mesh

def implicit_laplace_smooth(vertices: np.ndarray, M: scipy.sparse.sparray, S: scipy.sparse.sparray, tau: float) -> np.ndarray:
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
        x_i = vertices[:, i]
        # print("x_i: ", x_i[:100])
        M_i = M
        S_i = S
        MS = M_i + tau * S_i
        MX = M_i @ x_i
        x_i1 = scipy.sparse.linalg.spsolve(MS, MX)
        # print("x_i+1: ", x_i1[:100])
        # print("x_i: ", x_i.shape)
        # print("m_i: ", M_i.shape)
        # print("s_i: ", S_i.shape)
        # print("ms: ", MS.shape)
        # print("mx: ", MX.shape)
        # print("x_i1: ", x_i1.shape)
        vertices[:, i] = x_i1
    return vertices


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
        iterations: int
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
    for _ in range(iterations):
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

    # Compute mass matrix
    M, Mv = build_mass_matrices(mesh)
    m_inv = scipy.sparse.linalg.inv(M)

    # Compute gradient matrix
    G = build_gradient_matrix(mesh)

    # Compute cotangent matrix
    # S = build_cotangent_matrix(G, Mv)
    S = G.T @ Mv @ G

    # Compute Laplacian matrix
    L = m_inv @ S

    L2 = build_combinatorial_laplacian(mesh)

    # u = scipy.sparse.identity(S.shape[0], format='coo')
    # non = u.T @ S @ u


    print("L should be this::")
    print(L2)

    print("L:")
    print(L.toarray())

    print("m:")
    print(M.toarray())

    print("m_inv:")
    print(m_inv.toarray())

    print("G:")
    print(G.toarray())

    print("Mv:")
    print(Mv.toarray())

    print("S:")
    print(S.toarray())



    # assert np.allclose(L.toarray(), L2.toarray())


    # Perform smoothing operations
    for _ in range(iterations):
        # X = implicit_laplace_smooth(X, M, S, tau)
        X = explicit_laplace_smooth(X, L, tau)

    # Write smoothed vertices back to output mesh
    set_verts(mesh, X)

    return mesh
