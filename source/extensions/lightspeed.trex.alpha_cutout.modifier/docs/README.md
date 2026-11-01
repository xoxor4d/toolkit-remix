# lightspeed.trex.alpha_cutout.modifier

Registers the experimental **Alpha Card to Mesh** asset modifier. It cuts alpha-tested cards (foliage, grates,
fences) along the alpha channel of their diffuse texture so only the opaque area remains as geometry, and
disables alpha testing on the result so the runtime treats it as opaque.

## Responsibilities

- Declare the modifier (`AlphaCardToMesh`): its inputs, which prims it accepts, and the graph that processes its
  output through the asset pipeline and replaces the source reference.
- Read the project into the job in `build_graph`: the model-file path of every selected mesh, its diffuse texture
  and, for captures, a snapshot of the composed project material. A replacement (a Remix reference owner) keeps
  the materials of its file, so overrides authored under its reference prim still apply after the swap.
- Run the conversion in the Job Queue (`AlphaCardToMeshJob`): read the meshes from the model file, cut them on
  worker threads with progress per mesh, hand an unoptimized model to mesh optimization and report the face and
  vertex counts of every mesh before and after the cut (`ConversionReport`), which the Job Queue persists.
- Register the modifier with the asset modifier factory, and the report codecs with the job queue, for the
  extension lifetime.

## Non-Responsibilities

- Resolving the selection into model files and reference targets, the Asset Modifiers window, persisted input
  values, the Job Queue, the asset pipeline and reference Replace, Revert and Undo; the framework owns those.
- The cutting itself; `lightspeed.trex.alpha_cutout.core` owns the geometry and USD helpers.

## Architecture

- `is_compatible` accepts meshes, mesh asset rows and Remix reference prims, because the Selection panel selects
  the owning reference prim together with a mesh; non-mesh prims expand to the convertible meshes below them,
  each listed once.
- `AlphaCardToMesh.inputs` mirror the fields of `CutoutParameters`, grouped into Parameters, Thicken (including
  the rim normal smoothing, which only applies to a thickened mesh) and Normals, so
  `parameters_from_values(job.values)` rebuilds the parameters in the job.
- `build_graph` stores one entry per convertible mesh under `job.values["meshes"]`:
  `{"prim_path": <path inside the model file>, "texture": <absolute path>, "material": <snapshot or None>}`.
  Meshes are skipped when they are skinned, carry geometry subsets or have no diffuse texture; a source without
  any convertible mesh gets `job.skip_reason`. A File Path Constant source lists every textured mesh of the file.
- The job writes `cutout_<HASH>.usda` (or `cutout_<name>.usda` for other models) into its job directory with the
  textures staged beside it, absolute texture paths and bare MDL module names. A capture mesh file also gets its
  root prim renamed to that stem, because the Selection panel takes the first ancestor named like a capture
  mesh as the asset root and would otherwise present the cutout's inner prim without its reference. The job
  returns a `MeshOptimizationRequest`; `add_asset_optimization_jobs` appends the prepare, texture and mesh
  optimization jobs with `AssetReplaceApplyHandler` (or `SaveMeshMetadataHandler` without a target).
- A mesh that yields no geometry (opaque texture, nothing opaque at the threshold, undecodable texture) is
  copied unchanged; the job completes as skipped only when no mesh converted.
- Every converted mesh records its origin (`remix:alphaCutoutSource`, `remix:alphaCutoutSourcePrim` and
  `remix:alphaCutoutMaterialPrim`). Running the modifier on a published cutout reads those attributes, converts
  the original model again with the current project material, and swaps the cutout reference in place, so the
  original is never cut twice and never modified. The framework still publishes each run to its own folder.

## Known limitations

- The alpha test type is stored as the raw runtime value `7`, which the material property panel labels with the
  MDL enum name "Greater Or Equal".
- For captures the material snapshot is taken at run time; later edits to the captured material need a new run.
- Up-facing normals use the stage up axis in the model's own space, so instance rotations are not accounted for.
