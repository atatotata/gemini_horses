-- Test: ApplyRecipe.M.apply end-to-end with stubbed Lightroom SDK
package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path

local infoLines = {}
local logLines = {}

package.preload["Logger"] = function()
  return {
    info = function(msg, ...) table.insert(infoLines, string.format(msg, ...)) end,
    warn = function(...) table.insert(infoLines, "WARN: " .. string.format(...)) end,
  }
end
package.preload["LiveLog"] = function()
  return {
    write = function(msg, ...) table.insert(logLines, string.format(msg, ...)) end,
    clear = function() end,
  }
end
package.preload["Prefs"] = function()
  return { get = function() return nil end }
end

local beforeTable = {
  Exposure = 0, Temperature = 5200, Highlights = 0, ParametricShadows = 0,
  Vibrance = 0, EnableToneCurve = false, ToneCurvePV2012 = { 0, 0, 255, 255 },
}
local afterTable = {
  Exposure = 0.65, Temperature = 5800, Highlights = -35, ParametricShadows = 15,
  Vibrance = 0, EnableToneCurve = true, ToneCurvePV2012 = { 0, 0, 64, 52, 128, 128, 192, 208, 255, 255 },
}

local controllerValues = {
  Exposure = 0, Contrast = 0, Highlights = 0, Shadows = 0,
  Temperature = 5200, Vibrance = 0, Whites = 0, Blacks = 0,
}

_G.photo = nil
_G.import = function(name)
  if name == "LrApplication" then
    return {
      activeCatalog = function()
        return {
          getTargetPhoto = function() return _G.photo end,
          setSelectedPhotos = function() end,
          withWriteAccessDo = function(_self, _label, fn, _opts) fn() end,
          withReadAccessDo = function(_self, fn) fn() end,
        }
      end,
      addDevelopPresetForPlugin = function() return nil end,
    }
  elseif name == "LrApplicationView" then
    return {
      getCurrentModuleName = function() return "develop" end,
      switchToModule = function() end,
    }
  elseif name == "LrDevelopController" then
    return {
      getValue = function(k) return controllerValues[k] end,
      setValue = function(k, v) controllerValues[k] = v end,
      revealPanel = function() end,
      goToMasking = function() end,
      createNewMask = function() end,
      getSelectedMask = function() return 1 end,
      getMaskCount = function() return 2 end,
    }
  elseif name == "LrTasks" then
    return {
      sleep = function() end,
      startAsyncTask = function(fn) fn() end,
      execute = function() end,
    }
  end
  return {}
end

local ApplyRecipe = require "ApplyRecipe"

local photoState = "before"
local photo = {
  getFormattedMetadata = function() return "TEST_01.dng" end,
  getDevelopSettings = function()
    local copy = {}
    local src = (photoState == "before") and beforeTable or afterTable
    for k, v in pairs(src) do
      copy[k] = v
    end
    return copy
  end,
  applyDevelopSettings = function() photoState = "after" end,
  applyDevelopPreset = function() photoState = "after" end,
}
_G.photo = photo

local recipe = {
  settings = {
    Exposure = 0.65,
    Temperature = 5800,
    Highlights = -35,
    ParametricShadows = 15,
    ToneCurvePV2012 = { 0, 0, 64, 52, 128, 128, 192, 208, 255, 255 },
  },
  masks = nil,
}

local ok, msg, details = ApplyRecipe.apply(photo, recipe, {
  applyGlobals = true,
  applyMasks = false,
  applyCrop = false,
})
assert(ok, "apply failed: " .. tostring(msg) .. " | " .. tostring(details))
print("apply ok: " .. tostring(msg))

local joined = table.concat(infoLines, "\n")
local lj = table.concat(logLines, "\n")
print("---- infoLines ----")
print(joined)
print("---- logLines ----")
print(lj)

-- LiveLog header & footer
assert(lj:find("APPLY & DIFF PASS — target: TEST_01.dng", 1, true), "LiveLog header missing")
assert(lj:find("beforeSettings=true", 1, true), "header should report beforeSettings captured")
assert(lj:find("Apply & Diff pass finished: settings=true masks=0 crop=false", 1, true), "LiveLog footer missing")

-- Diff lines prove beforeSettings flowed through to RecipeDebugger.report
assert(joined:find("[DIFF] Exposure: 0.00 -> +0.65 (delta: +0.65)", 1, true), "diff Exposure missing")
assert(joined:find("[DIFF] Temperature: 5200 -> 5800 (delta: +600)", 1, true), "diff Temperature missing")
assert(joined:find("[DIFF] Highlights: 0 -> -35 (delta: -35)", 1, true), "diff Highlights missing")
assert(joined:find("[DIFF] ParametricShadows: 0 -> +15 (delta: +15)", 1, true), "diff ParametricShadows missing")
assert(joined:find("[DIFF] ToneCurvePV2012: [Linear] -> [Custom Point Curve (5 points)]", 1, true), "diff curve missing")
assert(joined:find("[DIFF] Masks applied: 2 AI masks active (planned 0)", 1, true), "mask summary missing")
assert(joined:find("[DEBUG] Globals Readback: total=4, verified=4, mismatched=0, missing=0", 1, true), "verify summary missing")
assert(joined:find("=== [AI Ref Match Apply & Diff Report] ===", 1, true), "report header missing")

-- beforeSettings was captured BEFORE controller wrote values: verify original values were used in diff
assert(joined:find("[DIFF] Exposure: 0.00 ->", 1, true), "before value should be 0.00 (captured pre-apply)")

print("ALL APPLYRECIPE TESTS PASSED")