"""
* SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
* SPDX-License-Identifier: Apache-2.0
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* https://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
"""

from __future__ import annotations

__all__ = ["mesh_label", "mesh_value", "summarize_report"]

from lightspeed.trex.alpha_cutout.modifier import ConversionReport, MeshReport

_SUMMARY_LINES = 4


def mesh_label(item: MeshReport) -> str:
    """Name a mesh by its path below the model's root prim, so meshes of one model stay distinguishable.

    Args:
        item: Report of one mesh.

    Returns:
        The path below the root prim, or the full path for a root-level prim.
    """
    parts = item.prim_path.strip("/").split("/")
    return "/".join(parts[1:]) if len(parts) > 1 else item.prim_path


def mesh_value(item: MeshReport) -> str:
    """Describe what the cut did to one mesh.

    Args:
        item: Report of one mesh.

    Returns:
        The face and vertex counts before and after the cut, or the skip reason.
    """
    if item.skip_reason:
        return f"Skipped: {item.skip_reason}"
    return f"{item.source_faces:,} -> {item.faces:,} faces, {item.source_vertices:,} -> {item.vertices:,} vertices"


def summarize_report(report: ConversionReport) -> str:
    """Describe a whole report in a few lines, one per mesh.

    Args:
        report: Report of one job.

    Returns:
        One line per mesh up to a short limit, then a count of the remaining meshes.
    """
    lines = [f"{mesh_label(item)}: {mesh_value(item)}" for item in report.meshes[:_SUMMARY_LINES]]
    remaining = len(report.meshes) - len(lines)
    if remaining > 0:
        lines.append(f"and {remaining} more mesh{'es' if remaining > 1 else ''}")
    return "\n".join(lines)
