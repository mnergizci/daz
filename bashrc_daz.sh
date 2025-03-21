#!/bin/bash
## Automatically detect daz path based on this script's location

export daz_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

## Remove any previous occurrences of the global DAZ paths from PATH and PYTHONPATH
export PATH=$(echo "$PATH" | awk -v RS=: -v ORS=: '$0 !~ "/gws/smf/j04/nceo_geohazards/software/comet_github/daz"' | sed 's/:$//')
export PYTHONPATH=$(echo "$PYTHONPATH" | awk -v RS=: -v ORS=: '$0 !~ "/gws/smf/j04/nceo_geohazards/software/comet_github/daz/lib"' | sed 's/:$//')

## Set paths explicitly and clearly
export PATH="$daz_path/bin:$PATH"
export PYTHONPATH="$daz_path/lib:$PYTHONPATH"
