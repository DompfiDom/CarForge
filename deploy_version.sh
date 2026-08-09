#!/bin/sh
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <git-repository> [deployment-directory]" >&2
    exit 2
fi

repository=$1
script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
deployment_directory=${2:-$script_directory}

if git -C "$repository" rev-parse --git-dir >/dev/null 2>&1; then
    git_command="worktree"
elif git --git-dir="$repository" rev-parse --git-dir >/dev/null 2>&1; then
    git_command="bare"
else
    echo "Kein Git-Repository gefunden: $repository" >&2
    exit 1
fi

if [ "$git_command" = "worktree" ]; then
    commit_count=$(git -C "$repository" rev-list --count HEAD)
    commit_hash=$(git -C "$repository" rev-parse --short HEAD)
else
    commit_count=$(git --git-dir="$repository" rev-list --count HEAD)
    commit_hash=$(git --git-dir="$repository" rev-parse --short HEAD)
fi

version="1.0.$commit_count ($commit_hash)"
temporary_file="$deployment_directory/.version.tmp"
version_file="$deployment_directory/.version"

printf '%s\n' "$version" > "$temporary_file"
mv -f "$temporary_file" "$version_file"
printf 'Version geschrieben: %s\n' "$version"
