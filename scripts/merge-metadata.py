#!/usr/bin/env python3
"""Merge a newly-published version into ant-android's maven-metadata.xml.

Gradle's `publishReleasePublicationToPagesRepository` regenerates
maven-metadata.xml listing ONLY the version it just published. This repo
(ant-maven) must instead keep the full history, so after copying the new
version directory in we merge: keep every existing <version>, add the new one,
and point <latest>/<release> at it. Then regenerate the metadata checksums.

Usage:
    merge-metadata.py <metadata.xml> <new-version> [<lastUpdated>]

<metadata.xml>  the ant-maven maven-metadata.xml to update in place (may not
                exist yet — treated as empty history).
<new-version>   e.g. 0.0.8
<lastUpdated>   optional 14-digit yyyymmddHHMMSS; defaults to keeping the
                existing value (or 0). The publish workflow passes gradle's
                fresh timestamp so the file matches what gradle emitted.
"""
import hashlib
import os
import re
import sys

TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<metadata>\n"
    "  <groupId>com.autonomi</groupId>\n"
    "  <artifactId>ant-android</artifactId>\n"
    "  <versioning>\n"
    "    <latest>{latest}</latest>\n"
    "    <release>{release}</release>\n"
    "    <versions>\n"
    "{versions}\n"
    "    </versions>\n"
    "    <lastUpdated>{last}</lastUpdated>\n"
    "  </versioning>\n"
    "</metadata>\n"
)


def version_key(v):
    return [int(p) if p.isdigit() else p for p in re.split(r"[.\-]", v)]


def main():
    if len(sys.argv) < 3:
        sys.exit(f"usage: {sys.argv[0]} <metadata.xml> <new-version> [<lastUpdated>]")
    path, new = sys.argv[1], sys.argv[2]

    existing = open(path).read() if os.path.exists(path) else ""
    versions = re.findall(r"<version>([^<]+)</version>", existing)
    if new not in versions:
        versions.append(new)
    versions = sorted(set(versions), key=version_key)

    if len(sys.argv) >= 4 and sys.argv[3]:
        last = sys.argv[3]
    else:
        m = re.search(r"<lastUpdated>(\d+)</lastUpdated>", existing)
        last = m.group(1) if m else "0"

    body = TEMPLATE.format(
        latest=new,
        release=new,
        versions="\n".join(f"      <version>{v}</version>" for v in versions),
        last=last,
    )
    open(path, "w").write(body)

    # Regenerate the sidecar checksums Pages consumers verify.
    raw = body.encode()
    for algo in ("md5", "sha1", "sha256", "sha512"):
        digest = hashlib.new(algo, raw).hexdigest()
        open(f"{path}.{algo}", "w").write(digest)

    print("versions now: " + ", ".join(versions) + f"  (latest={new})")


if __name__ == "__main__":
    main()
