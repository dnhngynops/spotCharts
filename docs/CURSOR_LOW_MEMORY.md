# Using Cursor on 8GB RAM (Tahoe / Low Memory)

If Cursor (especially with Claude Code) pushes "application memory" into tens of GB and your Mac crashes or freezes, use these steps.

## 1. Settings already applied (User settings.json)

- **diffEditor.maxComputationTime**: 5000 (stops huge diffs from using unbounded CPU/memory)
- **editor.minimap.enabled**: false
- **typescript.tsserver.maxTsServerMemory**: 1024 (1GB cap for TS/JS language server)
- **files.watcherExclude**: heavy dirs excluded (data/, output/, logs/, .git, venv, etc.)
- **search.followSymlinks**: false

Restart Cursor after any settings change.

## 2. Claude Code and big files (main cause of 44GB)

- **Close the biggest file when you don’t need it**  
  e.g. `templates/dashboard_template.html` (2700+ lines). Keep only the files you’re editing in the agent’s context.
- **Use @-mentions**  
  Reference specific files with `@filename` instead of leaving many files open so the model doesn’t pull in huge context.
- **Start a new chat for new tasks**  
  Long chats keep more context in memory; new chats use less.
- **Prefer Composer for small, focused edits**  
  Use Claude Code for smaller, targeted changes and avoid “edit the whole project” style requests when possible.

## 3. Launch Cursor with a memory cap (optional)

From terminal, so Node/Electron child processes are capped:

```bash
# If you have "cursor" in PATH (Install from Command Palette):
NODE_OPTIONS="--max-old-space-size=2048" cursor
```

Or run the script (from repo root):

```bash
chmod +x scripts/launch_cursor_low_memory.sh
./scripts/launch_cursor_low_memory.sh
```

Then use this launcher instead of the Dock/Spotlight when you need to avoid crashes. If it still crashes, try `1536` instead of `2048`.

## 4. Other tips for 8GB

- **Fewer tabs**: Close editors you’re not using.
- **Disable unused extensions**: Extensions (especially language servers) can use a lot of RAM. Try `cursor --disable-extensions` to see if things improve.
- **Clear old chat history**: Large chat history can increase memory. Clear or archive old conversations.
- **Restart Cursor regularly**: E.g. after a long Claude Code session, quit and reopen.
- **One Cursor window**: Avoid multiple Cursor windows if possible.

## 5. If it’s still unusable

On 8GB, Cursor + Claude Code can still be heavy. Options:

- Use Cursor for browsing/editing and run Claude Code only when needed, then close the panel.
- Use the web version of Claude for big conversations and Cursor for code only.
- Consider upgrading RAM if you rely on Cursor + AI daily.
