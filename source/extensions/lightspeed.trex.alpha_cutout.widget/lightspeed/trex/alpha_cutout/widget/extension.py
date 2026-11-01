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

__all__ = ["AlphaCutoutWidgetExtension"]

from omni.ext import IExt
from omni.flux.job_queue.widget import get_display_adapter_registry

from .display_adapter import AlphaCardToMeshDisplayAdapter
from .notifier import ConversionNotifier


class AlphaCutoutWidgetExtension(IExt):
    """Present the Alpha Card to Mesh job in the Job Queue and notify when one finishes, for the extension lifetime."""

    def __init__(self):
        """Hold the notifier until Kit starts the extension."""
        super().__init__()
        self._notifier: ConversionNotifier | None = None

    def on_startup(self, ext_id: str) -> None:
        """Register the display adapter and start listening for finished jobs.

        Args:
            ext_id: Extension id, unused.
        """
        get_display_adapter_registry().register(AlphaCardToMeshDisplayAdapter)
        self._notifier = ConversionNotifier()

    def on_shutdown(self) -> None:
        """Stop listening and unregister the display adapter."""
        if self._notifier is not None:
            self._notifier.destroy()
            self._notifier = None
        get_display_adapter_registry().unregister(AlphaCardToMeshDisplayAdapter)
