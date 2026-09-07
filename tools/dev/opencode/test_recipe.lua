-- Functional test: RecipeSchema sanitize/normalize + formatForDisplay
package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path

package.preload["Logger"] = function()
  local M = { info = function() end, warn = function() end, error = function() end }
  return M
end

local RS = require "RecipeSchema"

local recipe = {
  summary = "Match golden-hour reference look",
  confidence = 0.87,
  pipeline = "multi_agent",
  rationale = "Global Look: reference is 0.5 stop brighter and cooler; Exposure +0.35, Temperature -400K.\nTone Curve Intent: lifted blacks with gentle S-curve for the reference's filmic rolloff.\nColor Grading: teal shadows + amber highlights recreate the golden-hour split.",
  strategy = "Fix the sky first, then give the subject a gentle pop, then dim the background for separation.",
  critique = "Skin tones are natural after the -5 magenta refinement; highlights retain detail; masks harmonize with the global grade.",
  subagentNotes = {
    analyst = "Analyst note line one\nAnalyst note line two",
    colorist = "raw colorist json",
    maskSpecialist = "raw mask specialist json",
    masks = "raw mask specialist json",
    critic = "raw critic json",
  },
  directives = { "Set Exposure +0.35", "Create Sky mask: Highlights -40", "Set Point curve S-curve" },
  settings = {
    Exposure = 0.35,
    Contrast = -12,
    Temperature = 5600,
    Tint = 8,
    Vibrance = 15,
    ParametricHighlights = 20,
    ParametricShadows = -10,
    ParametricShadowSplit = 28,
    ParametricMidtoneSplit = 50,
    ParametricHighlightSplit = 72,
    ToneCurvePV2012 = { 0, 0, 64, 52, 128, 128, 192, 208, 255, 255 },
    HueAdjustmentBlue = -15,
    SaturationAdjustmentBlue = 25,
    SaturationAdjustmentOrange = -10,
    SplitToningShadowHue = 210,
    SplitToningShadowSaturation = 12,
    SplitToningHighlightHue = 40,
    SplitToningHighlightSaturation = 8,
    SplitToningBalance = -5,
    PostCropVignetteAmount = -15,
    EnableToneCurve = true,
    ToneCurveName2012 = "Custom",
  },
  masks = {
    {
      maskType = "sky",
      name = "Sky Recovery",
      purpose = "Sky is ~1 stop brighter than the reference; mask recovers cloud detail and shifts hue toward cyan.",
      adjustments = { Exposure = -0.35, Highlights = -40, Saturation = 15, Temperature = -8 },
    },
    {
      maskType = "subject",
      name = "Subject Pop",
      rationale = "Subject lacks separation from the background; gentle exposure and clarity lift.",
      adjustments = { Exposure = 0.25, Clarity = 10 },
    },
  },
  manualSteps = { "Optional brush on catchlights" },
}

local s = RS.sanitize(recipe)
assert(s.rationale == recipe.rationale, "rationale not preserved")
assert(s.strategy == recipe.strategy, "strategy not preserved")
assert(s.critique == recipe.critique, "critique not preserved")
assert(s.subagentNotes.maskSpecialist == "raw mask specialist json", "subagentNotes.maskSpecialist not preserved")
assert(s.subagentNotes.masks == "raw mask specialist json", "subagentNotes.masks not preserved")
assert(s.subagentNotes.analyst == recipe.subagentNotes.analyst, "analyst notes not preserved")
assert(s.masks[1].purpose == recipe.masks[1].purpose, "mask purpose not preserved")
assert(s.masks[2].rationale == recipe.masks[2].rationale, "mask rationale not preserved")
assert(s.masks[1].maskType == "sky", "mask type")
print("sanitize/normalize preservation: OK")

local n = RS.normalize(recipe)
assert(n.strategy == recipe.strategy and n.critique == recipe.critique, "normalize alias failed")
print("normalize alias: OK")

local txt = RS.formatForDisplay(s)
print("---------------- FORMATTED OUTPUT ----------------")
print(txt)
print("--------------------------------------------------")

assert(txt:find("AI COLORIST STRATEGY & RATIONALE", 1, true), "header 1 missing")
assert(txt:find("REGIONAL AI MASKS & PURPOSE", 1, true), "header 2 missing")
assert(txt:find("DEVELOP SETTINGS & SLIDERS", 1, true), "header 3 missing")
assert(txt:find("CRITIC & REFINEMENT EVALUATION", 1, true), "header 4 missing")
assert(txt:find("Global Look:", 1, true), "Global Look section missing")
assert(txt:find("Tone Curve Intent:", 1, true), "Tone Curve Intent section missing")
assert(txt:find("Color Grading:", 1, true), "Color Grading section missing")
assert(txt:find("Sky Recovery", 1, true), "mask name missing")
assert(txt:find("Sky is ~1 stop brighter", 1, true), "mask purpose missing")
assert(txt:find("Subject Pop", 1, true), "mask 2 missing")
assert(txt:find("Exposure: 0.35", 1, true), "formatted number missing")
assert(txt:find("ToneCurvePV2012", 1, true), "point curve missing")
assert(txt:find("Blue: H-15 S25", 1, true), "HSL compact format missing")
assert(txt:find("Mask Specialist Notes:", 1, true), "mask specialist notes missing")
print("formatForDisplay full recipe: OK")

-- Empty / minimal recipe must not error and must omit critic section
local e = RS.formatForDisplay(RS.sanitize({ summary = "x" }))
assert(not e:find("CRITIC & REFINEMENT"), "critic section should be absent when no critique")
assert(e:find("DEVELOP SETTINGS & SLIDERS"), "empty settings section missing")
print("formatForDisplay minimal recipe: OK")

print("ALL RECIPESCHEMA TESTS PASSED")