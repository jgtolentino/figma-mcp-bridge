#!/usr/bin/env bash
# Setup Claude Memory Modes - Global, Project, or Session-based
# Run this once to configure your Claude memory architecture

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧠 Claude Memory Architecture Setup${NC}"
echo "======================================"

# 1. Backup existing memories
echo -e "\n${YELLOW}📦 Step 1: Backing up existing memories...${NC}"
BACKUP_DIR="$HOME/infra/claude_memory_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -d "$HOME/.claude/projects" ]; then
    cp -r "$HOME/.claude/projects" "$BACKUP_DIR/"
    echo -e "${GREEN}✓ Backed up to: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}⚠ No existing projects directory found${NC}"
fi

# 2. Create memory structure
echo -e "\n${YELLOW}🏗 Step 2: Creating memory architecture...${NC}"
mkdir -p "$HOME/.claude/global_memory"
mkdir -p "$HOME/.claude/sessions"
mkdir -p "$HOME/.claude/project_contexts"

# 3. Consolidate existing memories
if [ -d "$HOME/.claude/projects" ] && [ ! -L "$HOME/.claude/projects" ]; then
    echo -e "\n${YELLOW}🔄 Step 3: Consolidating memories...${NC}"
    find "$HOME/.claude/projects" -type f -name '*.jsonl' -exec cp {} "$HOME/.claude/global_memory/" \; 2>/dev/null || true
    echo -e "${GREEN}✓ Consolidated $(find "$HOME/.claude/global_memory" -name '*.jsonl' | wc -l) conversation files${NC}"
fi

# 4. Create mode switcher
echo -e "\n${YELLOW}📝 Step 4: Creating mode switcher...${NC}"
cat > "$HOME/.claude/switch_mode.sh" << 'SCRIPT'
#!/usr/bin/env bash
# Switch Claude memory mode: global, project, or session

MODE="${1:-status}"
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

case "$MODE" in
    global)
        rm -f "$HOME/.claude/projects"
        ln -s "$HOME/.claude/global_memory" "$HOME/.claude/projects"
        echo -e "${GREEN}✓ Switched to GLOBAL memory mode${NC}"
        echo "All sessions now share the same memory"
        ;;
    
    project)
        rm -f "$HOME/.claude/projects"
        ln -s "$HOME/.claude/project_contexts" "$HOME/.claude/projects"
        echo -e "${BLUE}✓ Switched to PROJECT-based memory mode${NC}"
        echo "Each directory gets its own context"
        ;;
    
    session)
        echo -e "${YELLOW}✓ SESSION mode requires using launch_claude_session.sh${NC}"
        echo "Usage: ./launch_claude_session.sh <session-name>"
        ;;
    
    status|*)
        echo -e "${BLUE}Current Claude memory mode:${NC}"
        if [ -L "$HOME/.claude/projects" ]; then
            TARGET=$(readlink "$HOME/.claude/projects")
            case "$TARGET" in
                *global_memory*)
                    echo -e "${GREEN}→ GLOBAL${NC} (all sessions share memory)"
                    ;;
                *project_contexts*)
                    echo -e "${BLUE}→ PROJECT${NC} (directory-based isolation)"
                    ;;
                *sessions*)
                    echo -e "${YELLOW}→ SESSION${NC} (manual session isolation)"
                    ;;
                *)
                    echo "→ Custom: $TARGET"
                    ;;
            esac
        else
            echo "→ Default (legacy project-based)"
        fi
        echo -e "\nAvailable modes:"
        echo "  global  - All sessions share memory"
        echo "  project - Directory-based isolation (default)"
        echo "  session - Manual session isolation"
        ;;
esac
SCRIPT

chmod +x "$HOME/.claude/switch_mode.sh"

# 5. Set default mode
echo -e "\n${YELLOW}🎯 Step 5: Setting default mode...${NC}"
read -p "Choose default mode [global/project/keep]: " DEFAULT_MODE

case "$DEFAULT_MODE" in
    global)
        rm -f "$HOME/.claude/projects"
        ln -s "$HOME/.claude/global_memory" "$HOME/.claude/projects"
        echo -e "${GREEN}✓ Set to GLOBAL mode${NC}"
        ;;
    project)
        rm -f "$HOME/.claude/projects"
        ln -s "$HOME/.claude/project_contexts" "$HOME/.claude/projects"
        echo -e "${BLUE}✓ Set to PROJECT mode${NC}"
        ;;
    *)
        echo -e "${YELLOW}✓ Keeping existing configuration${NC}"
        ;;
esac

# 6. Create aliases
echo -e "\n${YELLOW}🔧 Step 6: Creating convenience aliases...${NC}"
cat >> "$HOME/.zshrc" << 'ALIASES'

# Claude Memory Management
alias claude-mode='~/.claude/switch_mode.sh'
alias claude-session='~/Documents/GitHub/figma-mcp-bridge/scripts/launch_claude_session.sh'
alias claude-global='~/.claude/switch_mode.sh global && claude'
alias claude-project='~/.claude/switch_mode.sh project && claude'
ALIASES

echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "\nAvailable commands:"
echo -e "  ${BLUE}claude-mode${NC}         - Check/switch memory mode"
echo -e "  ${BLUE}claude-global${NC}       - Launch with global memory"
echo -e "  ${BLUE}claude-project${NC}      - Launch with project isolation"
echo -e "  ${BLUE}claude-session NAME${NC} - Launch in isolated session"
echo -e "\nReload shell to use aliases: ${YELLOW}source ~/.zshrc${NC}"