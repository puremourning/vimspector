local separator = ' '


local function createMessage()
  local words = {}
  table.insert(words, 'Hello')
  table.insert(words, 'world')
  return table.concat(words, separator)
end


local function withEmphasis(func)
  return function()
    return func() .. '!'
  end
end


createMessage = withEmphasis(createMessage)

print(createMessage())
