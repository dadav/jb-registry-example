#!/usr/bin/env python3

import re
import sys
import logging
import yaml
import json
from typing import List
from tempfile import mkdtemp
from dataclasses import dataclass, field, asdict
from pathlib import Path
from operator import itemgetter

from git import Repo

VERSION_REGEX = re.compile(r"^\d+\.\d+(?:\.\d+)?$")

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

log = logging.getLogger(__name__)


@dataclass
class PackageVersion:
    version: str
    source: str


@dataclass
class Package:
    name: str
    description: str
    source: str
    _package_dir: str = field(default=".")
    versions: List[PackageVersion] = field(default_factory=list)

    def analyze(self):
        tmp = mkdtemp()
        repo = Repo.clone_from(self.source, tmp)

        branch, versions = (
            repo.active_branch,
            [
                version.name
                for version in Path(tmp).glob(f"{self._package_dir}/*")
                if version.is_dir() and VERSION_REGEX.match(version.name)
            ],
        )

        for v in sorted(versions):
            if self._package_dir != ".":
                pv = PackageVersion(
                    v, f"{self.source}/{self._package_dir}/{v}@{branch}"
                )
            else:
                pv = PackageVersion(v, f"{self.source}/{v}@{branch}")
            self.versions.append(pv)


def main(index: str) -> int:
    with open(index, "rt") as f:
        raw = f.read()

    yaml_data = yaml.load(raw, yaml.SafeLoader)

    result = list()

    for package in sorted(yaml_data["packages"], key=itemgetter("name")):
        if "package_dirs" in package:
            for subpackage in package["package_dirs"]:
                p = Package(
                    name=f"{package['name']}-{subpackage}",
                    description=f"{package['description']} ({subpackage})",
                    source=package["source"],
                    _package_dir=subpackage,
                )
                p.analyze()
                result.append(asdict(p))
        else:
            p = Package(**package)

            p.analyze()
            result.append(asdict(p))

    with open("_gen.json", "wt") as f:
        f.write(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log.error("Give the index filename as argument.")
        sys.exit(1)

    sys.exit(main(sys.argv[1]))
