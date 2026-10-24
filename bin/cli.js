#!/usr/bin/env node

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const REPO_URL =
  "https://github.com/gouthi/skillforge/archive/refs/heads/main.tar.gz";
const ARCHIVE_PREFIX = "skillforge-main";

const CYAN = "\x1b[36m";
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const BOLD = "\x1b[1m";
const NC = "\x1b[0m";

const PLATFORM_DIRS = {
  "claude-code": path.join(os.homedir(), ".claude", "skills"),
  cursor: path.join(os.homedir(), ".cursor", "skills"),
};

function usage() {
  console.log(`
${BOLD}skillforge${NC} — Install AI skills for Claude Code, Cursor, and more

${BOLD}Usage:${NC}
  npx skillforge install <group/skill>       Install a specific skill
  npx skillforge install <group>             Install all skills in a group
  npx skillforge install --all               Install everything
  npx skillforge list                        List available skills
  npx skillforge help                        Show this help

${BOLD}Options:${NC}
  --platform <p>   Target: claude-code (default), cursor, claude-ai
  --dir <path>     Custom install directory (overrides --platform)

${BOLD}Examples:${NC}
  npx skillforge install google-drive/gdrive-save
  npx skillforge install thinking-patterns
  npx skillforge install --platform cursor obsidian
  npx skillforge list
`);
}

function downloadAndExtract(tmpDir) {
  fs.mkdirSync(tmpDir, { recursive: true });
  try {
    execSync(`curl -sL "${REPO_URL}" | tar xz -C "${tmpDir}"`, {
      stdio: ["pipe", "pipe", "pipe"],
    });
  } catch {
    console.error(`${RED}✗${NC}  Failed to download skillforge repository.`);
    console.error("   Check your internet connection and try again.");
    process.exit(1);
  }
  return path.join(tmpDir, ARCHIVE_PREFIX, "skills");
}

function discoverSkills(skillsDir) {
  const groups = {};
  if (!fs.existsSync(skillsDir)) return groups;

  for (const groupName of fs.readdirSync(skillsDir)) {
    const groupPath = path.join(skillsDir, groupName);
    if (!fs.statSync(groupPath).isDirectory()) continue;

    groups[groupName] = [];
    for (const skillName of fs.readdirSync(groupPath)) {
      const skillPath = path.join(groupPath, skillName);
      const skillMd = path.join(skillPath, "SKILL.md");
      if (!fs.statSync(skillPath).isDirectory()) continue;
      if (!fs.existsSync(skillMd)) continue;

      let desc = "";
      const content = fs.readFileSync(skillMd, "utf-8");
      const match = content.match(
        /^description:\s*>?\s*\n?\s*(.+)/m
      );
      if (match) desc = match[1].trim();

      groups[groupName].push({ name: skillName, desc });
    }
  }
  return groups;
}

function listSkills(skillsDir) {
  const groups = discoverSkills(skillsDir);
  console.log("\nAvailable skills:\n");
  for (const [groupName, skills] of Object.entries(groups)) {
    if (skills.length === 0) continue;
    console.log(`  ${BOLD}${groupName}/${NC}`);
    for (const skill of skills) {
      const name = skill.name.padEnd(30);
      console.log(`    ${GREEN}${name}${NC} ${skill.desc}`);
    }
    console.log();
  }
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function installSkill(skillsDir, group, skill, destDir) {
  const src = path.join(skillsDir, group, skill);
  if (!fs.existsSync(src)) {
    console.error(`  ${RED}✗${NC}  Skill '${group}/${skill}' not found`);
    return false;
  }
  if (!fs.existsSync(path.join(src, "SKILL.md"))) {
    console.error(
      `  ${YELLOW}⚠${NC}  Skill '${group}/${skill}' has no SKILL.md — skipping`
    );
    return false;
  }

  const dest = path.join(destDir, skill);
  console.log(`  Installing ${GREEN}${group}/${skill}${NC} → ${dest}/`);
  copyDir(src, dest);
  console.log(`  ${GREEN}✓${NC}  ${group}/${skill} installed`);
  return true;
}

function installGroup(skillsDir, group, destDir) {
  const groupDir = path.join(skillsDir, group);
  if (!fs.existsSync(groupDir)) {
    console.error(`  ${RED}✗${NC}  Group '${group}' not found`);
    return false;
  }

  let installed = false;
  for (const entry of fs.readdirSync(groupDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const skillMd = path.join(groupDir, entry.name, "SKILL.md");
    if (!fs.existsSync(skillMd)) continue;
    installSkill(skillsDir, group, entry.name, destDir);
    installed = true;
  }

  if (!installed) {
    console.error(
      `  ${YELLOW}⚠${NC}  Group '${group}' has no installable skills`
    );
  }
  return installed;
}

function installAll(skillsDir, destDir) {
  for (const groupName of fs.readdirSync(skillsDir)) {
    const groupPath = path.join(skillsDir, groupName);
    if (!fs.statSync(groupPath).isDirectory()) continue;
    installGroup(skillsDir, groupName, destDir);
  }
}

function showClaudeAiInstructions() {
  console.log(`
${BOLD}claude.ai — Manual Upload Instructions${NC}

  claude.ai requires uploading skills as ZIP files.
  Requires a Pro, Max, Team, or Enterprise plan with code execution enabled.

  ${BOLD}Step 1: Package the skill as a ZIP${NC}

    cd skills/<group>
    zip -r <skill-name>.zip <skill-name>/

    The ZIP must contain the skill folder as its root:

      ${GREEN}Correct:${NC}  analogy-engine.zip → analogy-engine/SKILL.md
      ${RED}Wrong:${NC}    analogy-engine.zip → SKILL.md (files directly in root)

  ${BOLD}Step 2: Upload to claude.ai${NC}

    1. Open https://claude.ai
    2. Click ${CYAN}Customize${NC} (left sidebar)
    3. Click ${CYAN}Skills${NC} at the top
    4. Click the ${CYAN}+${NC} button → ${CYAN}Upload a skill${NC}
    5. Select your .zip file
    6. Toggle the skill on to activate it
`);
}

// --- Main ---

const args = process.argv.slice(2);
let platform = "claude-code";
let customDir = null;
const positional = [];

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--platform" && args[i + 1]) {
    platform = args[++i];
  } else if (args[i] === "--dir" && args[i + 1]) {
    customDir = args[++i];
  } else {
    positional.push(args[i]);
  }
}

const command = positional[0];

if (platform === "claude-ai") {
  showClaudeAiInstructions();
  process.exit(0);
}

if (!command || command === "help" || command === "--help" || command === "-h") {
  usage();
  process.exit(0);
}

const destDir = customDir || PLATFORM_DIRS[platform];
if (!destDir) {
  console.error(
    `${RED}✗${NC}  Unknown platform: ${platform}`
  );
  console.error("   Supported: claude-code, cursor, claude-ai");
  process.exit(1);
}

const tmpDir = path.join(os.tmpdir(), `skillforge-${Date.now()}`);

try {
  if (command === "list") {
    console.log("Fetching skill catalog...\n");
    const skillsDir = downloadAndExtract(tmpDir);
    listSkills(skillsDir);
  } else if (command === "install") {
    const targets = positional.slice(1);
    const installAll_ = targets.includes("--all");

    if (targets.length === 0 && !installAll_) {
      console.error(
        `${RED}✗${NC}  No skill or group specified.\n`
      );
      console.error("   Usage: npx skillforge install <group/skill|group|--all>");
      process.exit(1);
    }

    console.log(`Platform: ${CYAN}${platform}${NC}`);
    console.log(`Installing to: ${destDir}\n`);

    const skillsDir = downloadAndExtract(tmpDir);
    fs.mkdirSync(destDir, { recursive: true });

    if (installAll_) {
      installAll(skillsDir, destDir);
    } else {
      for (const target of targets) {
        if (target.includes("/")) {
          const [group, skill] = target.split("/", 2);
          installSkill(skillsDir, group, skill, destDir);
        } else {
          installGroup(skillsDir, target, destDir);
        }
      }
    }

    console.log(`\n${GREEN}Done.${NC} Skills installed to: ${destDir}`);
  } else {
    console.error(`${RED}✗${NC}  Unknown command: ${command}`);
    console.error("   Run 'npx skillforge help' for usage.");
    process.exit(1);
  }
} finally {
  if (fs.existsSync(tmpDir)) {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}
