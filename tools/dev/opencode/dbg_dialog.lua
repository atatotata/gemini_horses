package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path
local testDir = "C:\\TMP\\opencode\\logtest2"
os.execute('cmd /c rd /s /q "' .. testDir .. '" 2>nul & mkdir "' .. testDir .. '" 2>nul')
_G.WIN_ENV = true
local dialogs = {}
_G.import = function(name)
  if name == "LrPathUtils" then return { getStandardFilePath = function() return testDir end, child = function(p, n) return p .. "\\" .. n end }
  elseif name == "LrTasks" then return { execute = function() return false, "boom" end, sleep = function() end, startAsyncTask = function(fn) fn() end }
  elseif name == "LrShell" then return { openFilesInDefaultApp = function() error("default app boom") end }
  elseif name == "LrDialogs" then return { presentModalDialog = function(opts) table.insert(dialogs, opts) return "ok" end, message = function() end }
  elseif name == "LrView" then return { osFactory = function() return {
      control_spacing = function() return 6 end,
      column = function(props) return { kind = "column", props = props } end,
      static_text = function(props) return { kind = "static_text", props = props } end,
      scrolled_view = function(props) return { kind = "scrolled_view", props = props } end,
      bind = function(name) return { bound = name } end } end }
  elseif name == "LrBinding" then return { makePropertyTable = function() return {} end, bind = function() return {} end }
  elseif name == "LrFunctionContext" then return { callWithContext = function(_, fn) return fn({}) end }
  end
  return {}
end
package.preload["Logger"] = function() return { info = function() end, warn = function() end } end
local LiveLog = require "LiveLog"
local ok, err = pcall(function() LiveLog.viewInDialog() end)
print("viewInDialog pcall ok=", ok, "err=", tostring(err))
print("dialogs shown:", #dialogs)
