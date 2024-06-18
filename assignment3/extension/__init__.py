import bpy.props
import mathutils

from .smooth_brush import *
from .test import *



class LaplaceCoordinateDeformBase(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    # Input parameters
    matrix_selection_mode: bpy.props.EnumProperty(
        name="Matrix Selection Mode", description="Method for setting up the gradient transformation matrix A.",
        items=[
            ('CUSTOM', "Custom Matrix", ""),
            ('ROTATION', "Rotation", ""),
            ('SCALE', "Scale (X, Y, Z)", ""),
        ]
    )
    A_matrix: bpy.props.FloatVectorProperty(
        name="A (matrix)",
        description="Gradient Transformation Matrix",
        size=[3, 3],
        subtype='MATRIX',
        default=mathutils.Matrix.Identity(3)
    )
    A_rotation: bpy.props.FloatVectorProperty(
        name="A (rotation)",
        description="Gradient Transformation by Rotation",
        size=[3],
        subtype='DIRECTION',
        default=[0, 0, 1]
    )
    A_scale: bpy.props.FloatVectorProperty(
        name="A (scale)",
        description="Gradient Transformation by Scale",
        size=[3],
        subtype='XYZ_LENGTH',
        default=[1, 1, 1]
    )
    tau: bpy.props.FloatProperty(
        name="Tau",
        description="Weight for the deformation",
        default=1.0,
        min=0.0,
        max=1.0
    )

    # Output parameters
    status: bpy.props.StringProperty(
        name="Smoothing Status", default="Status not set"
    )

    def tau(self):
        return self.tau

    @classmethod
    def poll(cls, context):
        return (
                context.view_layer.objects.active is not None
                and context.view_layer.objects.active.type == 'MESH'
        )

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text="Object to deform: ")
        row.separator()
        row.prop(context.view_layer.objects, 'active', text="", expand=True, emboss=False)
        layout.separator()

        layout.prop(self, 'tau', text="Tau")

        layout.prop(self, 'status', text="Status", emboss=False)


class LaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.laplace_deform"
    bl_label = "Laplace coordinates Deformation"

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        active_object = context.view_layer.objects.active

        # Produce BMesh types to work with
        mesh = bmesh.new()
        mesh.from_mesh(active_object.data)

        # Gradient deformation expects a triangle mesh
        self.status = f"Ensuring mesh contains only tris"
        bmesh.ops.triangulate(mesh, faces=mesh.faces)

        # Apply the deformation
        self.status = f"Computing deformation"
        #TODO TAU
        laplace_deform(mesh, tau=self.tau)

        # Write the results back to the underlying mesh
        self.status = f"Updating Mesh"
        mesh.to_mesh(active_object.data)
        active_object.data.update()

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(LaplaceCoordinateDeform.bl_idname)


class ConstrainedLaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.constrained_laplace_deform"
    bl_label = "Constrained Laplace Coordinates Deformation"

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        active_object = context.view_layer.objects.active

        # Produce BMesh types to work with
        mesh = bmesh.from_edit_mesh(active_object.data)

        # Gradient deformation expects a triangle mesh
        self.status = f"Ensuring mesh contains only tris"
        bmesh.ops.triangulate(mesh, faces=mesh.faces)

        # Determine selected faces
        selected_face_indices = [f.index for f in mesh.faces if f.select]
        self.num_selected_faces = len(selected_face_indices)

        # Apply the deformation
        new_verts = constrained_laplace_deform(mesh, selected_face_indices, 0.1)

        # Update the original mesh
        self.status = f"Updating Mesh"
        set_verts(mesh, new_verts)
        bmesh.update_edit_mesh(active_object.data)

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(ConstrainedLaplaceCoordinateDeform.bl_idname)


def register():
    bpy.types.VIEW3D_MT_object.append(LaplaceCoordinateDeform.menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(ConstrainedLaplaceCoordinateDeform.menu_func)
    # TODO: If you created an operator that belongs in a particular menu, add its menu func here.
    #       For an example, you can see how the deformation operators are added in assignment3/deformation/__init__.py

    # TODO: If you have functionality which depends on global state, you can add that here
    #       For examples, see how boolean options are set up at the bottom of assignment2/planes/__init__.py
    #     bpy.types.VIEW3D_MT_object.append(LaplaceCoordinateDeform.menu_func)
    #     bpy.types.VIEW3D_MT_edit_mesh.append(ConstrainedLaplaceCoordinateDeform.menu_func)
    pass
#
#
# # TODO: Define operators, panels, etc.
#
# # NOTE: Nothing in the `extension` directory will be automatically graded,
# #       Feel free to structure your code however you prefer!
# #
# #       You should document anything you want graded in your report and short screen recording.
#
#
#
#
