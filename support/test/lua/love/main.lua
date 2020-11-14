if pcall(require, 'lldebugger') then
  require('lldebugger').start()
end

local rect = {0, 0, 64, 64}


function love.update(dt)
  rect[1] = rect[1] + 10 * dt
  rect[2] = rect[2] + 10 * dt
end


function love.draw()
  love.graphics.rectangle('fill', rect[1], rect[2], rect[3], rect[4])
end


function love.keypressed()
  love.event.quit()
end
