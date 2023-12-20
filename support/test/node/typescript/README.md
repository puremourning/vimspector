# Howto

Typescript is a great language (looking past dependency hells of the js
ecosystem and the immense pain of setting up projects). This example shows you
how to use vimspector with
[vscode-js-debug](https://github.com/microsoft/vscode-js-debug). I only could
make this combination work by using 'attach' as launch. This is the reason why
this guide will explain how to use it with 'attach'. For all available options
see [here](https://github.com/microsoft/vscode-js-debug/blob/main/OPTIONS.md#node-attach).

## Prerequisites

- Ensure you are using nodejs version 18 or 20 (was tested with these and these are
  LTS (dezember 2023).
- Ensure you have vscode-js-debug installed, check installation guides for
  nodejs of the vimspector repo on how to do so.
- Install dependencies `yarn` (can install yarn if you don't have it yet, `npm i -g yarn`)

## Debugging

- Build the project `yarn build`
- Start the node process with inspect-brk option in a separate terminal `node --inspect-brk ./dist/index.js`
- Open the typescript file with vim `vim ./src/index.ts`
- Set breakpoints at line 2 and 3 (standard key mapping F9)
- Run debugging (standard key mapping F5)
- Press F5 once again (you should see console log output)
- Press F5 once again (you should see another console log output)
- Done🎉
