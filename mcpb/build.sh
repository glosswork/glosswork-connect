#!/usr/bin/env bash
#
# Build the Glosswork Claude Desktop extension.
#
# This is a PINNED build, not a reproducible one. Packing the identical directory twice
# gives two files of the same size and byte count with different SHA-256 digests, so the
# digest printed below identifies the one file this run produced and nothing more. Do not
# compare it with a digest from a different run and read a difference as tampering.
#
# The build needs the network: `npm ci` fetches the pinned dependency tree and `npx --yes`
# fetches the packer.
#
# Both versions are literal constants, verified on npm on the day they were set, and a
# test asserts each is an exact version rather than a range.

set -euo pipefail

MCPB_VERSION="2.1.2"   # npm view @anthropic-ai/mcpb version, 2026-09-18

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# npm's default cache is not usable on every machine this is built on, and `npx` reaches
# for the same one `npm ci` does, so this is exported before either command rather than
# set on one of them. It sits outside `mcpb/` because everything inside `mcpb/` is packed
# into the bundle, and a cache in there would be shipped to every person who installs it.
export npm_config_cache="$HERE/../.cache/npm"
mkdir -p "$npm_config_cache"

rm -rf node_modules dist
npm ci --omit=dev
npx --yes "@anthropic-ai/mcpb@${MCPB_VERSION}" pack . dist/glosswork.mcpb

BUNDLE="$HERE/dist/glosswork.mcpb"
echo
echo "bundle:  $BUNDLE"
echo "bytes:   $(wc -c < "$BUNDLE" | tr -d ' ')"
echo "sha256:  $(shasum -a 256 "$BUNDLE" | cut -d' ' -f1)"
