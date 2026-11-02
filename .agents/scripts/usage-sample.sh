#!/usr/bin/env bash
# Record one Claude usage sample (5-hour and weekly window) for coworking pacing.
# Appends a JSON line to .agents/tmp/coworking/usage.ndjson and prints a one-line summary.
# Usage:   usage-sample.sh <label>      e.g. usage-sample.sh "before reviewer round 3"
# Read:    jq -r '[.t, .label, .h5, .week] | @tsv' .agents/tmp/coworking/usage.ndjson
# Needs caut (usage tracker) and jq; costs no model tokens.
set -euo pipefail
label=${1:?label}
root=$(git rev-parse --show-toplevel)
out="$root/.agents/tmp/coworking/usage.ndjson"
mkdir -p "$(dirname "$out")"
caut usage --provider claude --json | jq -c --arg label "$label" '
  (.data[0].usage // error("caut returned no Claude usage")) as $u
  | {t: (now | strftime("%Y-%m-%dT%H:%M:%SZ")), label: $label,
     h5: $u.primary.usedPercent, h5Reset: $u.primary.resetsAt,
     week: $u.secondary.usedPercent, weekReset: $u.secondary.resetsAt}' | tee -a "$out" |
  jq -r '"\(.t) 5h \(.h5)% (resets \(.h5Reset[0:16])Z) week \(.week)% (resets \(.weekReset[0:16])Z): \(.label)"'
