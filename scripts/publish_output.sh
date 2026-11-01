#!/usr/bin/env bash
# Publish generated files to the orphan `output` branch.
#
#   scripts/publish_output.sh <source dir> "<commit message>"
#
# Copies everything in <source dir> over the current contents of `output`,
# keeping files that other workflows publish there, then force-pushes a single
# fresh commit so the branch never accumulates history. Needs GITHUB_TOKEN and
# GITHUB_REPOSITORY in the environment (both are set inside GitHub Actions).
set -euo pipefail

SRC="$1"
MESSAGE="$2"
REMOTE="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
WORK="$(mktemp -d)"

if ! git clone -q --depth=1 --branch output "$REMOTE" "$WORK/out" 2>/dev/null; then
  echo "No output branch yet; creating it."
  git init -q -b output "$WORK/out"
  git -C "$WORK/out" remote add origin "$REMOTE"
fi

cp -r "$SRC"/. "$WORK/out"/
cd "$WORK/out"
git checkout -q --orphan fresh
git add -A
git -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    commit -q -m "$MESSAGE"
git push -q --force origin fresh:output
echo "Published $(git ls-files | wc -l) file(s) to output: $(git ls-files | tr '\n' ' ')"
