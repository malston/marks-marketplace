# bd-json.sh -- read bd's JSON output in one shape, whatever bd version wrote it.
#
# shellcheck shell=bash
#
# Sourced by epic-loop and label-findings, which both read bd list and bd show
# output. Not meant to be run on its own.

# bd emits a bare object, a single-element array, or -- since bd 1.2, which
# stamps "schema_version" -- a {"data": ..., "schema_version": N} envelope
# around either. Unwrap the envelope first, then reduce a single-element array
# to the object inside, so every read goes through one shape.
#
# A failure is reported as {"error": ..., "schema_version": N} with no data
# key at all, so the unwrap has to require "data" as well. Keying on
# schema_version alone turns that object into a null, the error becomes
# unreadable, and an unknown bead is reported as an unreadable type instead.
bd_json() {
    jq -r 'if type == "object" and has("schema_version") and has("data")
           then .data else . end
           | if type == "array" then .[0] else . end'
}

# The same unwrap for list subcommands, which keep their array.
bd_json_array() {
    jq 'if type == "object" and has("schema_version") and has("data")
        then .data else . end'
}
