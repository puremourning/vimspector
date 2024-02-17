# Howto

For debugging without jest, see ../typescript/README.md.
Uses babel to transpile the .ts and debug it directly.

## Prerequisites

- Ensure you are using nodejs version 18 or 20 (was tested with these and these are
  LTS (december 2023).
- Ensure you have vscode-js-debug installed, check installation guides for
  nodejs of the vimspector repo on how to do so.
- Install dependencies `yarn` (can install yarn if you don't have it yet, `npm i -g yarn`)

## Debugging

- Build the project `yarn build`
- Start the node process with inspect-brk option in a separate terminal `node --inspect-brk ./node_modules/jest-cli/bin/jest.js --runInBand`
- Open the typescript file with vim `vim ./src/add.spec.ts`
- Set breakpoints at line 6 and 7 (standard key mapping F9)
- Run debugging (standard key mapping F5)
- Now you can use F5 to step through the code.
- Done🎉
