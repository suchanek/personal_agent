#!/usr/bin/env bash
#
# setup_shared_personal_agent_data.sh
#
# Configure /Users/Shared/personal_agent_data so multiple users can read/write it
# via a shared group and inheritable ACLs on macOS.
#
# Usage:
#   sudo ./setup_shared_personal_agent_data.sh [groupname] [directory] [user1 user2 ...]
#
# Defaults:
#   groupname = pagent
#   directory = /Users/Shared/personal_agent_data
#
# Example:
#   sudo ./setup_shared_personal_agent_data.sh pagent /Users/Shared/personal_agent_data eric persagent
#

set -euo pipefail

DEFAULT_GROUP="pagent"
DEFAULT_DIR="/Users/Shared/personal_agent_data"

GROUP="${1:-$DEFAULT_GROUP}"
DIR="${2:-$DEFAULT_DIR}"
shift $(( $# > 0 ? 1 : 0 )) || true  # If at least one arg, we consumed group
shift $(( $# > 0 ? 1 : 0 )) || true  # If at least two args, we consumed dir

USERS=("$@")  # remaining args

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

echo "== Shared personal_agent_data setup =="
echo "  Target directory : $DIR"
echo "  Shared group     : $GROUP"
if ((${#USERS[@]} > 0)); then
  echo "  Users to add     : ${USERS[*]}"
else
  echo "  Users to add     : (none specified)"
fi
echo

# 1. Ensure directory exists
echo "-- Ensuring directory exists..."
mkdir -p "$DIR"

# 2. Ensure group exists (use dseditgroup, which is macOS-friendly)
echo "-- Ensuring group '$GROUP' exists..."
if dseditgroup -o check "$GROUP" >/dev/null 2>&1; then
  echo "   Group '$GROUP' already exists."
else
  echo "   Creating group '$GROUP'..."
  dseditgroup -o create "$GROUP"
fi

# 3. Add specified users to the group (if any)
if ((${#USERS[@]} > 0)); then
  echo "-- Adding users to group '$GROUP'..."
  for u in "${USERS[@]}"; do
    if id "$u" >/dev/null 2>&1; then
      echo "   Adding user '$u' to '$GROUP'..."
      dseditgroup -o edit -a "$u" -t user "$GROUP"
    else
      echo "   WARNING: user '$u' does not exist, skipping." >&2
    fi
  done
fi

# 4. Set directory ownership to root:GROUP
echo "-- Setting directory ownership to root:$GROUP..."
chown -R "root:$GROUP" "$DIR"

# 5. Set POSIX permissions:
#    - 2 (setgid) so new files inherit the group
#    - 7/7/5 so owner+group have rwx, others r-x
echo "-- Setting directory permissions (2775)..."
chmod -R 2775 "$DIR"

# 6. Apply ACL so group always has full RW access, inheritable
echo "-- Applying ACL for group '$GROUP'..."
chmod -R +a "group:$GROUP allow read,write,append,delete,add_file,add_subdirectory,file_inherit,directory_inherit" "$DIR"

echo
echo "== Done =="
echo "Directory '$DIR' is now:"
echo "  - Owned by root:$GROUP"
echo "  - Setgid (group inheritance) with mode 2775"
echo "  - ACL configured so group '$GROUP' has RW access on all files and subdirs"
echo
echo "To verify:"
echo "  ls -le $DIR"
