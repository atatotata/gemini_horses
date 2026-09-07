-- Functional test: SubagentPipeline multi_agent flow with stubbed backend
package.path = "C:/Users/Ota/Desktop/lightroom-ref-match/AIRefMatch.lrdevplugin/?.lua;" .. package.path

package.preload["Logger"] = function()
  local M = { info = function() end, warn = function() end }
  return M
end
package.preload["LiveLog"] = function()
  local M = { write = function() end }
  return M
end
package.preload["Prefs"] = function()
  local M = { get = function() return nil end }
  return M
end
package.preload["RecipeSchema"] = function()
  local M = {
    systemPrompt = function() return "SYSTEM_PROMPT" end,
    normalize = function(r) return r end,
  }
  return M
end
package.preload["OmniRouteClient"] = function()
  local M = {
    chatCompletion = function(opts)
      if opts.jsonMode then
        local sp = opts.systemPrompt or ""
        if sp:find("Regional Adjustment Specialist") then
          return {
            masks = {
              {
                maskType = "sky",
                name = "AI Sky Adjustment",
                purpose = "Sky is brighter than reference; recover detail.",
                adjustments = { Exposure = -0.35, Saturation = 15 },
              },
            },
            strategy = "Recover sky detail, then lift subject.",
          }, "RAW_MASK_TEXT", nil
        end
        return { summary = "final", masks = {} }, "RAW_FINAL_JSON", nil
      end
      return nil, "RAW_ANALYST_TEXT", nil
    end,
  }
  return M
end
package.preload["json"] = function()
  local M = { encode = function(t) return "JSON_ENCODED" end }
  return M
end

local P = require "SubagentPipeline"
print("SubagentPipeline loads OK")

local recipe, err = P.execute({
  referencePath = "C:/ref.jpg",
  targetPath = "C:/tgt.jpg",
  pipelineMode = "multi_agent",
})
assert(recipe, "execute failed: " .. tostring(err))
assert(recipe.pipeline == "multi_agent", "pipeline flag")
assert(recipe.subagentNotes.masks == "RAW_MASK_TEXT", "mask raw not captured in subagentNotes.masks")
assert(recipe.subagentNotes.maskSpecialist == "RAW_MASK_TEXT", "mask raw not captured in subagentNotes.maskSpecialist")
assert(recipe.subagentNotes.critic == "RAW_FINAL_JSON", "critic raw not captured")
assert(recipe.subagentNotes.analyst == "RAW_ANALYST_TEXT", "analyst raw not captured")
assert(recipe.strategy == "Recover sky detail, then lift subject.", "mask strategy not propagated to recipe.strategy")
assert(recipe.masks[1].maskType == "sky", "masks not applied from mask stage")
assert(recipe.masks[1].purpose == "Sky is brighter than reference; recover detail.", "mask purpose lost")
print("multi_agent flow: strategy + mask purpose + subagentNotes all captured OK")

-- two_pass fallback path still works
local r2, e2 = P.execute({
  referencePath = "C:/ref.jpg",
  targetPath = "C:/tgt.jpg",
  pipelineMode = "two_pass",
})
assert(r2, "two_pass failed: " .. tostring(e2))
print("two_pass flow: OK")

print("ALL SUBAGENTPIPELINE TESTS PASSED")