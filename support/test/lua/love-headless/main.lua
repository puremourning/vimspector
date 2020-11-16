if pcall(require, 'lldebugger') then
  require('lldebugger').start()
end

local time = 0

function love.update(dt)
  time = time + dt
  love.event.quit()
end
