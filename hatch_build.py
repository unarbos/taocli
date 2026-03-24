from __future__ import annotations

import os
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        del version
        if self.target_name != "wheel":
            return

        bundled_binaries = list(Path("src/taocli/bin").glob("**/agcli"))
        if not bundled_binaries:
            return

        build_data["pure_python"] = False
        build_data["reproducible"] = False

        wheel_tag = os.environ.get("TAOCLI_WHEEL_TAG")
        if wheel_tag:
            build_data["tag"] = wheel_tag
            build_data.pop("infer_tag", None)
        else:
            build_data["infer_tag"] = True
