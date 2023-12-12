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
    versions: List[PackageVersion] = field(default_factory=list)

    def analyze(self):
        tmp = mkdtemp()
        repo = Repo.clone_from(self.source, tmp)
        branch, versions = (
            repo.active_branch,
            [
                version.name
                for version in Path(tmp).glob("*")
                if version.is_dir() and VERSION_REGEX.match(version.name)
            ],
        )

        for v in versions:
            pv = PackageVersion(v, f"{self.source}/{v}@{branch}")
            self.versions.append(pv)


def main(index: str) -> int:
    with open(index, "rt") as f:
        raw = f.read()

    yaml_data = yaml.load(raw, yaml.SafeLoader)

    result = list()

    for package in yaml_data["packages"]:
        p = Package(**package)
        p.analyze()
        result.append(asdict(p))

    with open("_gen.json", "wt") as f:
        json.dump(result, f)

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log.error("Give the index filename as argument.")
        sys.exit(1)

    sys.exit(main(sys.argv[1]))
