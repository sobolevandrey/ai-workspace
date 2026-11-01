#!/usr/bin/env bash
# ai-workspace — установщик для macOS и Linux / installer for macOS and Linux
#   curl -fsSL https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.sh | bash
#   или / or:  git clone https://github.com/sobolevandrey/ai-workspace ~/.ai-workspace && ~/.ai-workspace/install.sh
set -e
REPO="${AIW_REPO:-https://github.com/sobolevandrey/ai-workspace.git}"
ENGINE="${AIW_ENGINE:-$HOME/.ai-workspace}"
OS="$(uname)"
YES=0; for a in "$@"; do [ "$a" = "--yes" ] && YES=1; done   # --yes: без вопросов (ставит нейросеть)
need() { command -v "$1" >/dev/null 2>&1; }
say()  { printf '%s\n' "$*"; }
ask()  { printf '%s ' "$1"; read -r REPLY </dev/tty || REPLY=""; }

say "=== ai-workspace ==="

if [ "$OS" = "Darwin" ]; then
  if ! xcode-select -p >/dev/null 2>&1; then
    say "Нужны Command Line Tools от Apple (git, python3). Сейчас откроется окно установки."
    say "Apple Command Line Tools are required (git, python3). An installer window will open."
    xcode-select --install || true
    say "После установки запусти эту команду ещё раз. / Re-run this command when it finishes."
    exit 0
  fi
fi

pkg_install() {
  if [ "$OS" = "Darwin" ]; then
    if ! need brew; then
      say "Устанавливаю Homebrew (попросит пароль от Мака) / Installing Homebrew (asks for your password)"
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/tty
      for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$("$b" shellenv)"; done
      grep -q 'brew shellenv' "$HOME/.zprofile" 2>/dev/null || echo 'eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"' >> "$HOME/.zprofile"
    fi
    brew install "$@"
  elif need apt-get; then sudo apt-get update -qq && sudo apt-get install -y "$@"
  elif need dnf;     then sudo dnf install -y "$@"
  elif need pacman;  then sudo pacman -S --noconfirm "$@"
  elif need zypper;  then sudo zypper install -y "$@"
  else say "Установи вручную / please install manually: $*"; exit 1; fi
}

need git     || pkg_install git
need python3 || pkg_install python3

if ! need npx && [ "$YES" = 1 ]; then
  say "Node.js не найден — доступ к файлам из Claude Desktop можно включить позже. / Node.js not found — file access from Claude Desktop can be enabled later."
  if [ "$OS" = "Darwin" ] && need brew; then brew install node || true; fi
elif ! need npx; then
  ask "Node.js нужен, чтобы Claude Desktop видел твои файлы (MCP). Установить? / Node.js lets Claude Desktop see your files (MCP). Install? [Y/n]"
  case "$REPLY" in n*|N*) ;; *) if [ "$OS" = "Darwin" ]; then pkg_install node; else pkg_install nodejs npm; fi ;; esac
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$HERE" ] && [ -f "$HERE/aiw.py" ]; then
  ENGINE="$HERE"
elif [ -d "$ENGINE/.git" ]; then
  git -C "$ENGINE" pull --ff-only -q
else
  git clone -q "$REPO" "$ENGINE"
fi

if [ ! -t 0 ] && ( : </dev/tty ) 2>/dev/null; then
  exec python3 "$ENGINE/aiw.py" setup "$@" </dev/tty      # запуск через curl | bash
else
  exec python3 "$ENGINE/aiw.py" setup "$@"
fi
