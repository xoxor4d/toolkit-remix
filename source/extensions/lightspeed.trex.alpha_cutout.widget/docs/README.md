# lightspeed.trex.alpha_cutout.widget

Presents the **Alpha Card to Mesh** job in the Job Queue and notifies when one finishes. The modifier itself lives in
`lightspeed.trex.alpha_cutout.modifier`; this extension only owns how its job is displayed.

## Responsibilities

- Register a display adapter for `AlphaCardToMeshJob` that keeps the generic Asset Modifier presentation (source,
  name, targets) and adds a **Converted meshes** section to the job details, listing the face and vertex counts
  of every handled mesh before and after the cut, or why a mesh was skipped.
- Post a notification with the same counts when a conversion job finishes, with a button that opens the Job
  Queue, so the result is visible without opening the job details.

## Non-Responsibilities

- The conversion, the job, and the report values; the modifier extension produces them.
- The Job Queue window, its details panel, and the adapter registry; `omni.flux.job_queue.widget` owns those.

## Architecture

- `AlphaCardToMeshDisplayAdapter` extends `AssetModifierDisplayAdapter` and is registered for the exact job type,
  so the registry resolves it before the generic modifier adapter. `get_detail_sections` reads the persisted
  `ConversionReport` from the job outputs and names each mesh by its path below the model's root prim, so the
  meshes of one model stay distinguishable.
- `ConversionNotifier` subscribes to the queue's job changes, which arrive on worker threads, coalesces them onto
  the UI loop like the queue widget does, and reports each finished conversion job once: its report as an
  information toast, a skipped job as a warning with the reasons, a failed job as a warning with the state reason.
- `report_text` formats a mesh report for both presentations.
