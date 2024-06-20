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

    tau: bpy.props.FloatProperty(
        name="Tau",
        description="Weight for the deformation",
        default=0.001,
        min=0.0,
        max=1.0
    )

    it: bpy.props.IntProperty(
        name="Iterations",
        description="Number of iterations",
        default=1,
        min=1
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
        layout.prop(self, 'it', text="Iterations")

        layout.prop(self, 'status', text="Status", emboss=False)

class ImplicitLaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.implicit_laplace_deform"
    bl_label = "Implicit Laplace coordinates Deformation"

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

        laplace_deform(mesh, tau=self.tau, it=self.it)

        # Write the results back to the underlying mesh
        self.status = f"Updating Mesh"
        mesh.to_mesh(active_object.data)
        active_object.data.update()

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(ImplicitLaplaceCoordinateDeform.bl_idname)

class ExplicitLaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.explicit_laplace_deform"
    bl_label = "Explicit Laplace coordinates Deformation"

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

        iterative_explicit_laplace_smooth(mesh, tau=self.tau, it=self.it)

        # Write the results back to the underlying mesh
        self.status = f"Updating Mesh"
        mesh.to_mesh(active_object.data)
        active_object.data.update()

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(ExplicitLaplaceCoordinateDeform.bl_idname)


class ImplicitConstrainedLaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.implicit_constrained_laplace_deform"
    bl_label = "Implicit Constrained Laplace Coordinates Deformation"

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
        constrained_implicit_laplace_deform(mesh, selected_face_indices, self.tau, self.it)

        # Update the original mesh
        self.status = f"Updating Mesh"
        # set_verts(mesh, new_verts)
        bmesh.update_edit_mesh(active_object.data)

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(ImplicitConstrainedLaplaceCoordinateDeform.bl_idname)

class ExplicitConstrainedLaplaceCoordinateDeform(LaplaceCoordinateDeformBase):
    bl_idname = "object.explicit_constrained_laplace_deform"
    bl_label = "Explicit Constrained Laplace Coordinates Deformation"

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
        constrained_explicit_laplace_deform(mesh, selected_face_indices, self.tau, self.it)

        # Update the original mesh
        self.status = f"Updating Mesh"
        # set_verts(mesh, new_verts)
        bmesh.update_edit_mesh(active_object.data)

        self.status = f"Done"
        return {'FINISHED'}

    @staticmethod
    def menu_func(menu, context):
        menu.layout.operator(ExplicitConstrainedLaplaceCoordinateDeform.bl_idname)


def register():
    bpy.types.VIEW3D_MT_object.append(ImplicitLaplaceCoordinateDeform.menu_func)
    bpy.types.VIEW3D_MT_object.append(ExplicitLaplaceCoordinateDeform.menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(ImplicitConstrainedLaplaceCoordinateDeform.menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(ExplicitConstrainedLaplaceCoordinateDeform.menu_func)
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
