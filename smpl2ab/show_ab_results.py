# # Copyright (C) 2024  Max Planck Institute for Intelligent Systems Tuebingen, Marilyn Keller 

# import argparse
# import os
# import numpy as np
# import yaml

# from aitviewer.renderables.osim import OSIMSequence
# from aitviewer.renderables.smpl import SMPLSequence
# from aitviewer.renderables.markers import Markers
# from aitviewer.viewer import Viewer
# from aitviewer.models.smpl import SMPLLayer

# import config as cg
# from smpl2ab.markers.smpl_markers import SmplMarker
# from smpl2ab.utils.smpl_utils import load_smpl_seq

# if __name__ == "__main__":

#     parser = argparse.ArgumentParser()
    
#     parser.add_argument('--osim_path', type=str, help='Path to OpenSim model (.osim)')
#     parser.add_argument('--mot_path', type=str,  help='Path to OpenSim motion (.mot)')
#     parser.add_argument('--smpl_motion_path', type=str,  help='Path to SMPL motion')
#     parser.add_argument('--smpl_markers_path', type=str, default=cg.bsm_markers_on_smpl_path, help='Path to SMPL markers')
#     parser.add_argument('--body_model', help='Body model to use (smpl or smplx)', default='smpl', choices=['smpl', 'smplx'])
#     parser.add_argument('--gender', type=str, default=None, choices=['female', 'male', 'neutral'])
#     parser.add_argument('--z_up', action='store_true', help='Set the z axis up')
     
#     args = parser.parse_args()
    
#     to_display = []
    
#     if args.body_model == 'smpl':
#         body_model = 'smpl'
#     else :
#         body_model = args.body_model
        
#     if args.gender is None:
#         smpl_data = load_smpl_seq(args.smpl_motion_path)
#         gender = smpl_data['gender']
#     else:
#         gender = args.gender
        
#     smpl_layer = SMPLLayer(model_type=body_model, gender=gender)
#     args = parser.parse_args()
    
#     to_display = []
    
#     fps = 30 

#     # Load SMPL motion
#     seq_smpl = SMPLSequence.from_amass(
#         smpl_layer = smpl_layer,
#         npz_data_path=os.path.join(args.smpl_motion_path), # AMASS/CMU/01/01_01_poses.npz
#         fps_out=fps,
#         name=f"{args.body_model.upper()} motion",
#         show_joint_angles=False,
#         z_up=args.z_up
#     )
#     to_display.append(seq_smpl)
   
#     # Load result OpenSim motion
#     osim_seq = OSIMSequence.from_files(osim_path=args.osim_path, 
#                                        mot_file=args.mot_path, 
#                                        name=f'OpenSim skeleton motion', 
#                                        fps_out = fps,
#                                        color_skeleton_per_part=False, 
#                                        show_joint_angles=False, 
#                                        is_rigged=False,
#                                        ignore_fps=True,
#                                        ignore_geometry=True,
#                                        z_up=args.z_up)
    
#     to_display.append(osim_seq)


#     # Load SMPL markers
#     markers_dict = yaml.load(open(args.smpl_markers_path, 'r'), Loader=yaml.FullLoader)
#     synthetic_markers = SmplMarker(seq_smpl.vertices, markers_dict, fps=fps, name='Markers')
#     markers_seq = Markers(synthetic_markers.marker_trajectory, markers_labels=synthetic_markers.marker_names, 
#                           name='SMPL markers',
#                           color=(0, 1, 0, 1),
#                           z_up=args.z_up)
#     to_display.append(markers_seq)
    

#     # Display in the viewer
#     v = Viewer()
#     v.run_animations = True
#     v.scene.camera.position = np.array([10.0, 2.5, 0.0])
#     v.scene.add(*to_display)
    
#     if seq_smpl is not None:
#         v.lock_to_node(seq_smpl, (2, 0.7, 2), smooth_sigma=5.0)
#     v.playback_fps = fps
    
#     v.run()

# Copyright (C) 2024  Max Planck Institute for Intelligent Systems Tuebingen, Marilyn Keller 
# Headless render version: export video instead of opening an interactive window.

import argparse
import os
import numpy as np
import yaml

# ---- Headless / EGL setup (must happen BEFORE importing aitviewer or moderngl_window) ----
os.environ.setdefault("PYGLET_HEADLESS", "1")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
os.environ.setdefault("AITVIEWER_WINDOW", "headless")

# Monkey-patch moderngl-window headless window to force EGL + create an offscreen FBO
from moderngl_window.context import headless as mglw_headless
def _init_mgl_context_egl(self):
    import moderngl
    # Create standalone EGL context
    self._ctx = moderngl.create_standalone_context(backend='egl')
    # Create and bind an offscreen framebuffer
    self._fbo = self._ctx.simple_framebuffer((self.width, self.height), components=4)
    self._fbo.use()
    self._ctx.viewport = (0, 0, self.width, self.height)
mglw_headless.window.Window.init_mgl_context = _init_mgl_context_egl
# -----------------------------------------------------------------------------------------

from aitviewer.headless import HeadlessRenderer
from aitviewer.renderables.osim import OSIMSequence
from aitviewer.renderables.smpl import SMPLSequence
from aitviewer.renderables.markers import Markers
from aitviewer.models.smpl import SMPLLayer

import config as cg
from smpl2ab.markers.smpl_markers import SmplMarker
from smpl2ab.utils.smpl_utils import load_smpl_seq


def main():
    parser = argparse.ArgumentParser("Render SMPL + OpenSim motion headlessly to a video.")
    parser.add_argument('--osim_path', type=str, required=True, help='Path to OpenSim model (.osim)')
    parser.add_argument('--mot_path', type=str, required=True, help='Path to OpenSim motion (.mot)')
    parser.add_argument('--smpl_motion_path', type=str, required=True, help='Path to AMASS-style SMPL motion (.npz)')
    parser.add_argument('--smpl_markers_path', type=str, default=cg.bsm_markers_on_smpl_path, help='Path to SMPL markers .yml/.yaml')
    parser.add_argument('--body_model', default='smpl', choices=['smpl', 'smplx'], help='Body model type')
    parser.add_argument('--gender', type=str, default=None, choices=['female', 'male', 'neutral'])
    parser.add_argument('--z_up', action='store_true', help='Use Z-up coordinates')
    # headless export options
    parser.add_argument('--out', type=str, required=True, help='Output video path, e.g. out.mp4 / out.webm')
    parser.add_argument('--width', type=int, default=1280, help='Render width')
    parser.add_argument('--height', type=int, default=720, help='Render height')
    parser.add_argument('--fps_out', type=int, default=30, help='Output video FPS')
    parser.add_argument('--save_frames', type=str, default=None, help='Optional: directory to also dump per-frame PNGs')
    args = parser.parse_args()

    # Resolve gender from SMPL motion if not provided
    if args.gender is None:
        smpl_data_meta = load_smpl_seq(args.smpl_motion_path)
        gender = smpl_data_meta.get('gender', 'neutral')
    else:
        gender = args.gender

    smpl_layer = SMPLLayer(model_type=args.body_model, gender=gender)

    # Choose a consistent FPS for all sequences (display/export)
    fps = args.fps_out

    to_display = []

    print("fps", fps)
    # Load SMPL motion (AMASS-style .npz)
    seq_smpl = SMPLSequence.from_amass(
        smpl_layer=smpl_layer,
        npz_data_path=args.smpl_motion_path,  # e.g., AMASS/CMU/01/01_01_poses.npz
        fps_out=fps,
        name=f"{args.body_model.upper()} motion",
        show_joint_angles=False,
        z_up=args.z_up
    )
    to_display.append(seq_smpl)

    # Load OpenSim motion (skeleton only, geometry ignored for speed)
    osim_seq = OSIMSequence.from_files(
        osim_path=args.osim_path,
        mot_file=args.mot_path,
        name='OpenSim skeleton motion',
        fps_out=fps,
        color_skeleton_per_part=False,
        show_joint_angles=False,
        is_rigged=False,
        ignore_fps=True,
        ignore_geometry=True,
        z_up=args.z_up
    )
    to_display.append(osim_seq)

    # Load SMPL markers and create a Markers renderable
    markers_dict = yaml.load(open(args.smpl_markers_path, 'r'), Loader=yaml.FullLoader)
    synthetic_markers = SmplMarker(seq_smpl.vertices, markers_dict, fps=fps, name='Markers')
    markers_seq = Markers(
        synthetic_markers.marker_trajectory,
        markers_labels=synthetic_markers.marker_names,
        name='SMPL markers',
        color=(0, 1, 0, 1),
        z_up=args.z_up
    )
    to_display.append(markers_seq)

    # ---- Headless renderer (no GUI) ----
    r = HeadlessRenderer(width=args.width, height=args.height)
    r.playback_fps = fps
    r.scene.add(*to_display)

    # Camera & follow (best-effort; ignore if not supported)
    try:
        r.scene.camera.position = np.array([10.0, 2.5, 0.0])
    except Exception:
        pass
    try:
        r.lock_to_node(seq_smpl, (2, 0.7, 2), smooth_sigma=5.0)
    except Exception:
        pass

    # Export video (this save_video signature matches your installed aitviewer-skel)
    r.save_video(
        frame_dir=args.save_frames,   # None or a folder to dump PNGs
        video_dir=args.out,           # e.g. "out.mp4" / "out.webm"
        output_fps=args.fps_out,      # output fps
        transparent=False             # only respected for .webm
    )
    print(f"[Headless] Saved video to: {args.out}")
    if args.save_frames:
        print(f"[Headless] Saved frames to: {args.save_frames}")


if __name__ == "__main__":
    main()
