import scipy

import mathutils

from assignment3.matrices.util import *
from assignment3.matrices.differential_coordinates import *


# !!! This function will be used for automatic grading, don't edit the signature !!!
def gradient_deform(mesh: bmesh.types.BMesh, A: mathutils.Matrix) -> np.ndarray:
    """
    Deforms a mesh by applying a transformation to its gradient vectors and then updating its vertices to match.

    This can be done with the help of the gradient, mass, and cotangent matrix functions from part 1.
    First find new gradients for the mesh by applying the transformation matrix A to its existing gradients,
    then use a sparse solver (from scipy) to find new vertices which match the target gradients.
    For more information, see the slides.

    :param mesh: The mesh to be modified.
    :param A: A 3x3 transformation matrix to apply to the gradients.
    :return: An Nx3 matrix representing new vertex positions for the mesh.
    """
    # TODO: Deform the gradients of the mesh and find new vertices.
    verts = numpy_verts(mesh)
    faces = numpy_faces(mesh)
    
    # Compute the gradient matrix
    G = compute_gradient_matrix(mesh)
    
    # Apply transformation A to the gradients
    G_transformed = G @ verts @ A.transposed()
    
    # Compute the mass and cotangent matrices
    M = compute_mass_matrix(mesh)
    C = compute_cotangent_matrix(mesh)
    
    # Solve for new vertex positions
    L = C @ G
    rhs = M @ G_transformed
    
    new_verts = scipy.sparse.linalg.spsolve(L, rhs)
    return new_verts


# !!! This function will be used for automatic grading, don't edit the signature !!!
def constrained_gradient_deform(
        mesh: bmesh.types.BMesh,
        selected_face_indices: list[int],
        A: mathutils.Matrix
) -> np.ndarray:
    """
    Deforms a mesh by applying a transformation to the gradient vectors of the selected triangles,
    and then updating its vertices to match.

    This can be done with the help of the gradient, mass, and cotangent matrix functions from part 1.
    First find new gradients by applying the transformation matrix to the gradients of only the selected triangles,
    then use a sparse solver (from scipy) to find new vertices which match the target gradients.
    For more information, see the slides.

    :param mesh: The mesh to be modified.
    :param selected_face_indices: List of indices indicating for which faces gradients should be changed.
    :param A: A 3x3 transformation matrix to apply to the gradients.
    :return: An Nx3 matrix representing new vertex positions for the mesh.
    """
    # TODO: Deform the gradients of the mesh and find new vertices.
    verts = numpy_verts(mesh)
    faces = numpy_faces(mesh)
    
    # Compute the gradient matrix
    G = compute_gradient_matrix(mesh)
    
    # Apply transformation A only to the selected gradients
    G_transformed = G.copy()
    for face_index in selected_face_indices:
        G_transformed[face_index] = G[face_index] @ A.transposed()
    
    # Compute the mass and cotangent matrices
    M = compute_mass_matrix(mesh)
    C = compute_cotangent_matrix(mesh)
    
    # Solve for new vertex positions
    L = C @ G
    rhs = M @ G_transformed
    
    new_verts = scipy.sparse.linalg.spsolve(L, rhs)

    return new_verts
