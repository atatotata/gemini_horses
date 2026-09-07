-- Test: LiveLog.openWindow fallback chain + ShowLiveLog wiring
package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path

local testDir = "C:\\TMP\\opencode\\logtest"
os.execute('cmd /c rd /s /q "' .. testDir .. '" 2>nul & mkdir "' .. testDir .. '" 2>nul')

_G.WIN_ENV = true

local executed = {}
local executeResult = true
local executeErr = nil
local openedDefault = {}
local defaultAppThrows = false
local dialogs = {}

_G.import = function(name)
  if name == "LrPathUtils" then
    return {
      getStandardFilePath = function() return testDir end,
      child = function(parent, name) return parent .. "\\" .. name end,
    }
  elseif name == "LrTasks" then
    return {
      execute = function(cmd)
        table.insert(executed, cmd)
        return executeResult, executeErr
      end,
      sleep = function() end,
      startAsyncTask = function(fn) fn() end,
    }
  elseif name == "LrShell" then
    return {
      openFilesInDefaultApp = function(path)
        table.insert(openedDefault, path)
        if defaultAppThrows then error("default app boom") end
      end,
    }
  elseif name == "LrDialogs" then
    return {
      presentModalDialog = function(opts) table.insert(dialogs, opts) return "ok" end,
      message = function() end,
    }
  elseif name == "LrView" then
    return {
      osFactory = function()
        return {
          control_spacing = function() return 6 end,
          column = function(props) return { kind = "column", props = props } end,
          static_text = function(props) return { kind = "static_text", props = props } end,
          scrolled_view = function(props) return { kind = "scrolled_view", props = props } end,
        }
      end,
      bind = function(name) return { bound = name } end,
    }
  elseif name == "LrBinding" then
    return {
      makePropertyTable = function() return {} end,
      bind = function() return {} end,
    }
  elseif name == "LrFunctionContext" then
    return { callWithContext = function(_, fn) return fn({}) end }
  end
  return {}
end

package.preload["Logger"] = function()
  return { info = function() end, warn = function() end, debug = function() end }
end

local LiveLog = require "LiveLog"
local logPath = testDir .. "\\AIRefMatch_live.log"
local psPath = testDir .. "\\AIRefMatch_live_tail.ps1"

-- ---- 1. ensureExists creates the file with a header ----
local ok, err = LiveLog.ensureExists()
assert(ok, "ensureExists failed: " .. tostring(err))
local f = io.open(logPath, "r")
assert(f, "log file not created")
local firstWrite = f:read("*a")
f:close()
assert(firstWrite:find("=== AI Reference Match Live Activity Log ===", 1, true), "header missing")
print("1. ensureExists creates header: OK")

-- ---- 2. write() on existing file appends; header only once ----
LiveLog.write("hello world %d", 42)
local content = LiveLog.readAll()
assert(content:find("[", 1, true) and content:find("hello world 42", 1, true), "write failed")
local headerCount = 0
local idx = 1
while true do
  local s = content:find("=== AI Reference Match Live Activity Log ===", idx, true)
  if not s then break end
  headerCount = headerCount + 1
  idx = s + 1
end
assert(headerCount == 1, "header duplicated: " .. headerCount)
print("2. write appends, single header: OK")

-- ---- 3. write() on a MISSING file prepends the header ----
os.remove(logPath)
LiveLog.write("fresh write")
content = LiveLog.readAll()
assert(content:find("=== AI Reference Match Live Activity Log ===", 1, true), "header not prepended on fresh write")
assert(content:find("fresh write", 1, true), "fresh write missing")
print("3. write() prepends header on missing file: OK")

-- ---- 4. openWindow success path: PowerShell tail launch ----
executeResult = true
executed = {}
ok, err = LiveLog.openWindow()
assert(ok, "openWindow failed: " .. tostring(err))
assert(#executed == 1, "expected 1 execute call, got " .. #executed)
local cmd = executed[1]
assert(cmd:find('start "" powershell.exe', 1, true), "cmd does not use start + powershell: " .. cmd)
assert(cmd:find('-ExecutionPolicy Bypass -File "' .. psPath .. '"', 1, true), "cmd does not launch the ps1 file: " .. cmd)
assert(#openedDefault == 0, "should not fall back to editor")
local pf = io.open(psPath, "r")
assert(pf, "tail script not written")
local psScript = pf:read("*a")
pf:close()
assert(psScript:find("Get-Content -Wait -Tail 50 -LiteralPath '" .. logPath .. "'", 1, true), "ps1 missing Get-Content with log path")
assert(not psScript:find("`n", 1, true), "ps1 should not contain literal backtick-n")
print("4. openWindow launches tail via start + -File: OK")
print("   cmd: " .. cmd)

-- ---- 5. openWindow fallback: execute fails -> default editor ----
executeResult = false
executeErr = "boom"
openedDefault = {}
ok, err = LiveLog.openWindow()
assert(ok, "openWindow should succeed via editor fallback: " .. tostring(err))
assert(#openedDefault == 1 and openedDefault[1] == logPath, "editor fallback did not open the log path")
print("5. fallback to default editor: OK (" .. tostring(err) .. ")")

-- ---- 6. openWindow last resort: execute fails AND editor throws -> in-app dialog ----
defaultAppThrows = true
dialogs = {}
ok, err = LiveLog.openWindow()
assert(ok, "openWindow should succeed via dialog viewer: " .. tostring(err))
assert(#dialogs == 1, "dialog viewer not shown")
assert(dialogs[1].title:find("Live Activity Log", 1, true), "dialog title wrong")
assert(dialogs[1].width == 720 and dialogs[1].height == 500, "dialog size wrong")
print("6. last-resort in-app dialog viewer: OK")

-- ---- 7. openWindow total failure reports false ----
defaultAppThrows = true
executeResult = false
local savedImport = _G.import
-- force viewInDialog context failure via broken stub
_G.import = function(name)
  if name == "LrFunctionContext" then
    return { callWithContext = function() error("no context") end }
  end
  return nil
end
-- revert import, then monkey-patch viewInDialog to throw
_G.import = savedImport
ok, err = LiveLog.openWindow()
assert(ok, "openWindow should still report success via dialog: " .. tostring(err))
print("7. dialog path (stub intact): OK")
-- Now force the dialog to fail
local savedView = LiveLog.viewInDialog
LiveLog.viewInDialog = function() error("dialog boom") end
ok, err = LiveLog.openWindow()
assert(not ok, "openWindow should report failure when every viewer fails")
assert(err:find("All log viewers failed", 1, true), "failure message wrong: " .. tostring(err))
LiveLog.viewInDialog = savedView
print("8. total failure reports false with details: OK")

-- ---- 9. Validate the generated .ps1 parses in real PowerShell ----
LiveLog.ensureExists()
local launchOk, launchErr = LiveLog.openWindow() -- regenerate ps1 via success path
local pf = io.open(psPath, "r")
assert(pf, "ps1 missing")
psScript = pf:read("*a")
pf:close()
local psCmd = string.format(
  "powershell.exe -NoLogo -NoProfile -Command \"$null = [scriptblock]::Create((Get-Content -Raw -LiteralPath '%s'))\"",
  psPath:gsub("'", "''")
)
-- direct check: run and capture
local out = io.popen(psCmd .. " 2>&1 & echo EXITCODE=%ERRORLEVEL%", "r")
local pso = out:read("*a")
out:close()
assert(not pso:find("ParserError", 1, true) and not pso:find("error", 1, true), "PS parse failed: " .. pso)
print("9. real PowerShell parse of tail script: OK")

-- ---- 10. ShowLiveLog menu flow loads and runs ----
dialogs = {}
executed = {}
executeResult = true
local okLoad, sl = pcall(require, "ShowLiveLog")
assert(okLoad, "ShowLiveLog failed to load: " .. tostring(sl))
assert(#executed >= 1, "ShowLiveLog did not trigger a launch")
print("10. ShowLiveLog menu flow: OK")

print("ALL LIVELOG TESTS PASSED")