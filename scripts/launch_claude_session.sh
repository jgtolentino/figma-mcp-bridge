#!/usr/bin/env bash
# Claude Session Manager - Switch between global and isolated session modes
# USAGE: ./launch_claude_session.sh [session-name] [claude-args...]
#        ./launch_claude_session.sh global    # Use global memory
#        ./launch_claude_session.sh mysession # Use isolated session

SESSION_NAME="${1:-default}"
shift

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Handle special modes
if [ "$SESSION_NAME" = "global" ]; then
    echo -e "${GREEN}✓ Using global memory mode${NC}"
    # Ensure global memory is linked
    if [ ! -L "$HOME/.claude/projects" ] || [ "$(readlink "$HOME/.claude/projects")" != "$HOME/.claude/global_memory" ]; then
        rm -rf "$HOME/.claude/projects"
        ln -s "$HOME/.claude/global_memory" "$HOME/.claude/projects"
    fi
    exec claude "$@"
    exit 0
fi

if [ "$SESSION_NAME" = "list" ]; then
    echo -e "${BLUE}Available sessions:${NC}"
    ls -1 "$HOME/.claude/sessions/" 2>/dev/null || echo "No sessions found"
    echo -e "\n${YELLOW}Current mode:${NC}"
    if [ -L "$HOME/.claude/projects" ]; then
        echo "→ $(readlink "$HOME/.claude/projects")"
    else
        echo "→ Default project-based context"
    fi
    exit 0
fi

# Create session directory
TARGET="$HOME/.claude/sessions/${SESSION_NAME}"
mkdir -p "$TARGET"

echo -e "${BLUE}🔒 Switching to isolated session: ${SESSION_NAME}${NC}"

# Backup current projects pointer
if [ -e "$HOME/.claude/projects" ]; then
    if [ ! -e "$HOME/.claude/projects.bak" ]; then
        mv "$HOME/.claude/projects" "$HOME/.claude/projects.bak"
    fi
fi

# Link to session directory
ln -sf "$TARGET" "$HOME/.claude/projects"

# Create session info file
cat > "$TARGET/.session_info" << EOF
Session: $SESSION_NAME
Created: $(date)
Purpose: Isolated context for focused work
EOF

# Launch Claude
echo -e "${GREEN}▶ Launching Claude in session mode...${NC}"
claude "$@"
EXIT_CODE=$?

# Restore original projects pointer
echo -e "${YELLOW}↩ Restoring previous memory mode...${NC}"
rm -f "$HOME/.claude/projects"
if [ -e "$HOME/.claude/projects.bak" ]; then
    mv "$HOME/.claude/projects.bak" "$HOME/.claude/projects"
fi

echo -e "${GREEN}✓ Session ended${NC}"
exit $EXIT_CODE