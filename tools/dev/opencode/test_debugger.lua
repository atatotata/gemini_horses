-- Test: RecipeDebugger.report before/after diff + verification
package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path

_G.import = function(name)
  if name == "LrDevelopController" then
    return { getMaskCount = function() return 3 end }
  end
  return {}
end

local infoLines = {}
package.preload["Logger"] = function()
  return {
    info = function(msg, ...) table.insert(infoLines, string.format(msg, ...)) end,
    warn = function() end,
  }
end
package.preload["LiveLog"] = function()
  return { write = function() end, clear = function() end }
end

local RD = require "RecipeDebugger"

local beforeSettings = {
  Exposure = 0,
  Temperature = 5200,
  Highlights = 0,
  ParametricShadows = 0,
  Vibrance = 10,
  EnableToneCurve = false,
  ToneCurvePV2012 = { 0, 0, 255, 255 },
  Contrast = -5,
}

local afterSettings = {
  Exposure = 0.65,
  Temperature = 5800,
  Highlights = -35,
  ParametricShadows = 15,
  Vibrance = 10,
  EnableToneCurve = true,
  ToneCurvePV2012 = { 0, 0, 64, 52, 128, 128, 192, 208, 255, 255 },
  Contrast = -5,
}

local photo = {
  getDevelopSettings = function()
    local copy = {}
    for k, v in pairs(afterSettings) do
      copy[k] = v
    end
    return copy
  end,
}

local recipe = {
  settings = {
    Exposure = 0.65,
    Temperature = 5800,
    Highlights = -35,
    ParametricShadows = 15,
    ToneCurvePV2012 = { 0, 0, 64, 52, 128, 128, 192, 208, 255, 255 },
  },
  masks = {
    { maskType = "sky", name = "Sky Recovery", adjustments = { Exposure = -0.35 } },
  },
}

local details = { settings = true, masks = 1, crop = false }

RD.report(photo, recipe, details, beforeSettings)

local joined = table.concat(infoLines, "\n")
print(joined)
print("----------------")

local function has(s)
  if not joined:find(s, 1, true) then
    error("MISSING: " .. s, 2)
  end
end

-- Exact formats from the task spec
has("[DIFF] Exposure: 0.00 -> +0.65 (delta: +0.65)")
has("[DIFF] Temperature: 5200 -> 5800 (delta: +600)")
has("[DIFF] Highlights: 0 -> -35 (delta: -35)")
has("[DIFF] ParametricShadows: 0 -> +15 (delta: +15)")
has("[DIFF] ToneCurvePV2012: [Linear] -> [Custom Point Curve (5 points)]")
-- unchanged keys must NOT appear
assert(not joined:find("Vibrance", 1, true) or joined:find("[DIFF] Vibrance", 1, true) == nil, "Vibrance should not be diffed")
assert(not joined:find("[DIFF] Contrast", 1, true), "Contrast should not be diffed")
-- verify pass: all expected matched -> no [VERIFY] lines, summary logged
has("[DEBUG] Globals Readback: total=4, verified=4, mismatched=0, missing=0")
-- mask summary with active count from getMaskCount stub
has("[DIFF] Masks applied: 3 AI masks active (planned 1)")
-- masks planned list
has("[DEBUG] Masks Planned (1 masks):")
-- summary count line
has("[DIFF] Settings changed: 6 key(s)")
print("diff/verify/mask assertions: OK")

-- Case 2: mismatched expected settings -> [VERIFY] line with off-by delta
infoLines = {}
local recipe2 = {
  settings = { Exposure = 0.75, Temperature = 5800 },
}
RD.report(photo, recipe2, { settings = true, masks = 0, crop = false }, beforeSettings)
local j2 = table.concat(infoLines, "\n")
assert(j2:find("[VERIFY] Exposure: expected +0.75, actual +0.65 (off by +0.10)", 1, true), "verify mismatch line missing:\n" .. j2)
assert(j2:find("[DEBUG] Globals Readback: total=2, verified=1, mismatched=1, missing=0", 1, true), "readback summary missing:\n" .. j2)
print("verify mismatch assertions: OK")

-- Case 3: no beforeSettings -> graceful skip, no crash
infoLines = {}
RD.report(photo, recipe2, nil, nil)
assert(table.concat(infoLines, "\n"):find("No beforeSettings captured", 1, true), "graceful skip missing")
print("no-beforeSettings graceful path: OK")

print("ALL RECIPEDEBUGGER TESTS PASSED")